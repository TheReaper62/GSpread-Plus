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
        self.listed = None
        self.sheet = None
        self.to_update = []

    def connect_sheet(self,name="Sheet1",index=None):
        if self.spread == None:
            raise InvalidMethod("Not Connected to Document")
            return
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
        else:
            # Intialize listed on sheet connection
            self.listed = self.sheet.get_all_values()

    def refresh_sheet(self):
        self.listed = self.sheet.get_all_values()

    def search_rowbycolumn(self,value,column="A",mode="static"):
        if self.sheet == None:
            raise InvalidMethod("No Sheet Specified")
            return

        if mode == "dynamic":
            self.listed = self.sheet.get_all_values()
        elif mode == "static":
            pass
        else:
            raise InvalidMethod("Methods Available: 'dynamic' 'static'")

        if str(column).startswith("-"):
            if column[1:] not in self.listed[0]:
                raise NotFound(f"Headername '{column[1:]}' not found")
                return
            col_index = self.listed[0].index(column[1:])+1
        elif type(column)==str:
            col_index = gspread.utils.a1_to_rowcol(f"{column}1")[0]
        elif column>0 and type(column)==int:
            col_index = column
        elif column==0:
            raise InvalidMethod("Column Indexing starts from 1 not 0")
        else:
            raise InvalidMethod("Invalid Column identifier")

        active_col = [i[col_index] for i in self.listed]
        if value in active_col:
            return self.listed[active_col.index(value)]

    def search_listed(self,value,mode="static",limits=None):
        if mode == "dynamic":
            self.listed = self.sheet.get_all_values()
        elif mode == "static":
            pass
        else:
            raise InvalidMethod("Methods Available: 'dynamic' 'static'")

        if limits==None:
            for i in self.listed:
                if value in i:
                    return [self.listed.index(i)+1,i.index(value)+1]
            return None
        else:
            if limits.startswith("-"):
                if limits not in self.listed[0]:
                    raise NotFound("Headername not found")
                    return
                col_index = self.listed[0].index(limits)+1
            elif limits.isalpha():
                row,col_index = gspread.utils.a1_to_rowcol(f"{limits}1")
            else:
                raise InvalidMethod("Invalid Limit")

            to_check = [i[col_index-1] for i in self.listed]
            if value in to_check:
                return to_check.index(value)+1
            return None

    def append_toupdate(self,position,value):
        # Syntax: new row F dynamic
        if str(position).startswith("new row"):
            if position.endswith("dynamic"):
                a1_not = f"{position.split()[2].upper()}{len(self.sheet.col_values(1))+1}"
            elif position.endswith("static"):
                a1_not = f"{position.split()[2].upper()}{len(self.listed)+1}"

        elif str(position[0]).isalpha() and str(position[-1]).isdigit():
            a1_not = position
        elif len(position)==2 and type(position[0]) and type(position[1]):
            a1_not = gspread.utils.rowcol_to_a1(position[0],position[1])
        row,col = gspread.utils.a1_to_rowcol(a1_not)
        element = gspread.models.Cell(row=row,col=col,value=value)
        self.to_update.append(element)

    def append_row_toupdate(self,row,values):
        # Syntax: new row dynamic
        if str(row).startswith("new row"):
            if row.endswith("dynamic"):
                row = len(self.sheet.col_values(1))+1
            elif row.endswith("static"):
                row = len(self.listed)+1
            else:
                raise InvalidMethod("Mode Not Stated. Example: 'new row dynamic'")

        for i in range(len(values)):
            self.to_update.append(gspread.models.Cell(row=row,col=i+1,value=values[i]))

    def push_toupdate(self):
        self.sheet.update_cells(self.to_update)
        self.listed = self.sheet.get_all_values()
        self.to_update = []

    def a1_rowcol_convert(self,value,to):
        if to=="rowcol":
            return gspread.utils.a1_to_rowcol(value)
        elif to=="a1":
            return gspread.utils.rowcol_to_a1(value)
        else:
            raise InvalidMethod("Available Methods: 'rowcol' 'a1'")

    def get_header_pos(self,headername,mode="static"):
        if mode == "dynamic":
            self.listed = self.sheet.get_all_values()
        elif mode == "static":
            pass
        else:
            raise InvalidMethod("Methods Available: 'dynamic' 'static'")

        if headername not in self.listed[0]:
            raise NotFound(f"Headername '{headername}' not found")
            return
        col_index = self.listed[0].index(headername)+1
        return col_index

    def delete_row_existence(self,row):
        self.sheet.delete_row(row)
        self.listed = self.sheet.get_all_values()
