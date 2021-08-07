from oauth2client.service_account import ServiceAccountCredentials
import gspread

class NotFound(Exception):
    pass
class InvalidMethod(Exception):
    pass

class Spreadclient:
    def __init__(self,credentials):
        creds = ServiceAccountCredentials.from_json_keyfile_name(credentials, ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive'])
        self.client = gspread.authorize(creds)
        self.spread = None
        self.sheet = None

    def connect_document(self,identifier,method='key'):
        if method.lower() == 'key':
            self.spread = self.client.open_by_key(identifier)
        elif method.lower() == 'name':
            self.spread = self.client.open(identifier)
        elif method.lower() == 'url':
            self.spread = self.client.open_by_url(identifier)
        else:
            raise InvalidMethod("Methods available: 'key' 'name' 'url'")

    def connect_sheet(self,name="Sheet1",index=None):
        if name!="Sheet1" and index!=None:
            raise InvalidMethod("Only use  name  or  index")
            return
        if index==None:
            self.sheet = self.spread.worksheet(name)
            identifier = f"Name '{name}'"
        elif type(index) == int:
            self.sheet = self.spread.get_worksheet(index)
            identifier = f"Index < {index} >"
        if self.sheet == None:
            raise NotFound(f"Sheet with the {identifier} Not Found")

    def search_rowbycolumn(self,value,column="A"):
        if type(column)==str:
            col_index = gspread.utils.a1_to_rowcol(f"{column}1")[0]
        elif column>0 and type(column)==int:
            col_index = column
        elif column==0:
            raise InvalidMethod("Column Indexing starts from 1 not 0")
        else:
            raise InvalidMethod("Invlaid Column identifier")
        active_col = self.sheet.col_values(col_index)
        if value in active_col:
            return self.sheet.row_values(active_col.index(value)+1)
