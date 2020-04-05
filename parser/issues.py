import datetime
import urllib


FILE_URL = "https://raw.githubusercontent.com/Crossroadsman/TechQuirksAndIssues/master/issues.txt"
FILENAME = "../issues.txt"


class Issue:
    
    def __init__(
        self,
        ID,
        title,
        date_filed,
        observed_on,
        keywords,
        search_query,
        solution_summary,
        solution_url,
        status,
        comments=[],
        **kwargs
    ):
        self.ID = ID
        self.title = title
        self.date_filed = date_filed
        self.observed_on = observed_on
        self.keywords = keywords
        self.search_query = search_query
        self.solution_summary = solution_summary
        self.solution_url = solution_url
        self.status = status
        self.comments = comments
        
        for key, value in kwargs:
            setattr(self, key, value)

    def __str__(self):
        return f'{self.ID}: {self.title}'

    def __repr__(self):
        return f'{self.ID}: {self.title}'


class IssueParser:
    
    state_in_record = False
    current_issue = {}
    issues = []
    
    def read_file(self, filename):
        with open(filename) as fh:
            for i, line in enumerate(fh):
                self.parse_line(line, i+1)
        
        if self.current_issue != {}:  # file didn't end with `''`, last issue still open
            print(f'attempting to write final issue: {self.current_issue}')
            self.issues.append(Issue(**self.current_issue))
            self.current_issue = {}
            self.state_in_record = False
        return self.issues

    def read_url(self, url):
        # Requires file to be in UTF-8
        file_data = urllib.request.urlopen(url)
        for i, line in enumerate(file_data):
            self.parse_line(line.decode('utf-8'), i+1)
        if self.current_issue != {}:  # file didn't end with `''`, last issue still open
            print(f'attempting to write final issue: {self.current_issue}')
            self.issues.append(Issue(**self.current_issue))
            self.current_issue = {}
            self.state_in_record = False
        return self.issues

    def parse_line(self, line, line_number=None):
        if line_number:
            print(f'PARSING LINE #{line_number}: {line}')
        else:
            print(f"PARSING LINE: {line}")

        if not self.state_in_record:
            print("Not in a record")
            # Wait until we get to a line that initiates a record
            # (or EOF)
            # - ID:
            # - new record marker
            # - EOF
            if line == '--------\n':
                print("new record marker")
                self.state_in_record = True
            elif line == '':
                print("EOF")
            else:  # check for ID
                print("checking if ID...")
                key, colon, value = line.partition(':')
                if key == 'ID':
                    print("...yes")
                    self.state_in_record = True
                    self.handle_id(value)
            
        else:  # we are in a record
            print("in a record")
            # 1. Check if we are exiting a record
            # - EOF (line='')
            # - new record marker
            # if so, create an issue from `current_issue` and append it
            # to `issues`
            if line in (
                '--------\n',
                '',
            ):
                print(f"attempting to write: {self.current_issue}")
                self.issues.append(Issue(**self.current_issue))
                self.current_issue = {}
                if line == '':
                    self.state_in_record = False
                return
            
            # not new record marker nor EOF:
            # 2. Otherwise handle the line
            if line[0] == "#":
                print(f'Line parsed as comment: {line}')
                self.handle_comment(line)
                return

            print(f'partitioning line: {line}')
            key, colon, value = line.partition(':')
            key = key.lower().replace(' ','_')
            if colon:
                expected_handler = f'handle_{key}'
                print(f'looking for handler: {expected_handler}...')

                if hasattr(self, expected_handler):
                    print('...found')
                    handler = getattr(self, expected_handler)
                    handler(value)
                    
                else:  # no specific handler
                    print('...not found, using generic handler')
                    self.handle_generic(key, value)
                return
            
            else:  # ignore the line
                print(f"ignoring line: {line}")
    
    # Handlers (text -> object)
    # -------------------------
    def handle_generic(self, key, value):
        self.current_issue[key] = value

    def handle_comment(self, value):
        list_ = self.current_issue.setdefault('comments', [])
        list_.append(value)

    def handle_id(self, value):
        try:
            ID = int(value)
        except ValueError:
            raise ValueError(
                f'ID must be coerceable into an integer, "{value}" was supplied'
            )
        else:
            self.current_issue['ID'] = ID

    def handle_title(self, value):
        self.current_issue['title'] = value

    def handle_date_filed(self, value):
        DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"
        dt = datetime.datetime.strptime(value.strip(), DATE_FORMAT)
        self.current_issue['date_filed'] = dt

    def handle_observed_on(self, value):
        self.current_issue['observed_on'] = value

    def handle_keywords(self, value):
        l = value.split(",")
        l = [x.strip().strip('"') for x in l]
        self.current_issue['keywords'] = l

    def handle_google_query(self, value):
        self.current_issue['search_query'] = value

    def handle_solution_summary(self, value):
        self.current_issue['solution_summary'] = value
        
    def handle_solution_url(self, value):
        self.current_issue['solution_url'] = value

    def handle_status(self, value):
        self.current_issue['status'] = value


# Example Usage:
#
ip = IssueParser()
issues = ip.read_file(FILENAME)  # for local file
# issues = ip.read_url(FILE_URL)  # for remote file

# `issues` is a list of `Issue` objects.
issues[0].date_filed  # a tz-aware datetime object
