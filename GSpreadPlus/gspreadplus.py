from __future__ import annotations
from typing import Union, Optional, Callable, Any

from oauth2client.service_account import ServiceAccountCredentials
import gspread

from .errors import IdentificationError

__all__ = (
    'Spreadclient',
)

# Decorator to check if object has requirements
def requirements_exists(*requirements):
    def decorator(func):
        def wrapper(*args, **kwargs):
            nonlocal requirements
            if requirements[0]=='*':
                requirements = ['client','document','sheet']
            if args[0].client == None and 'client' in requirements:
                raise Exception("Client has not been initialised")
            if args[0].document == None and 'document' in requirements:
                raise Exception("Document has not been connected")
            if args[0].sheet == None and 'sheet' in requirements:
                raise Exception("Sheet within document has not been connected")
            return func(*args,**kwargs)
        return wrapper
    return decorator

class Spreadclient:
    def __init__(self,credentials: Union[str,dict[str,str]]):
        SCOPES = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
        # Name of Credentials File (.json)
        if isinstance(credentials,str):
            creds = ServiceAccountCredentials.from_json_keyfile_name(credentials, SCOPES)
        # Dictionary of Credentials
        elif isinstance(credentials,dict):
            creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials, SCOPES)
        self.client = gspread.authorize(creds)
        self.document = None
        self.sheet = None
        self.listed = None
        self.commits = []

    @requirements_exists('client')
    def connect_document(self,identifier):
        methods = [self.client.open_by_key,self.client.open,self.client.open_by_url]
        for method in methods:
            try:
                self.document = method(identifier)
                if self.document == None:
                    raise Exception("Document Not Found")
                break
            except:
                pass
        else:
            raise Exception("Document identifier did not fit one of the formats (key,name,url)")

        self.listed = None
        self.sheet = None
        self.commits = []

    @requirements_exists('client','document')
    def connect_sheet(self,identifier:str="Sheet1",orientation:str='vertical',header_depth:int=1):
        if isinstance(identifier,str):
            self.sheet = self.document.worksheet(identifier)
            identifier = f"Name '{identifier}'"
        elif isinstance(identifier,int):
            self.sheet = self.document.get_worksheet(identifier)
            identifier = f"Index < {identifier} >"

        self.orientation = orientation
        self.header_depth = header_depth
        
        if self.sheet == None:
            raise IdentificationError(f"Sheet with the {identifier} Not Found")
        else:
            # Intialize listed on sheet connection
            self.refresh_sheet()

    @requirements_exists('*')
    def refresh_sheet(self):
        if len(self.commits) > 0:
            self.sheet.update_cells(self.commits)
            self.commits = []
        self.listed = self.sheet.get_all_values()

    @requirements_exists('*')
    def get_row_by_column(self, value: Union[str, int], column: Union[str, int] = 0, refresh: bool = False)->list[Any]:
        if refresh:
            self.refresh_sheet()
        # Pythonic Indexing
        if isinstance(column, str) and column.isalpha():
            index = gspread.utils.a1_to_rowcol(f"{column.upper()}1")[0] - 1
        elif isinstance(column, int):
            index = column
        else:
            raise Exception(f"Invalid Column identifier of type '{type(column)}'")
        for row in self.listed:
            if row[index] == value:
                return row
        return None

    @requirements_exists('*')
    def get_rows_by_func(self, function: Callable, refresh: bool = False)->list[Any]:
        match = []
        for row in self.listed:
            if function(row):
                match.append(row)
        return match

    @requirements_exists('*')
    def get_column_by_row(self, value: Union[str, int], row: int = 0, refresh: bool = False):
        if refresh:
            self.refresh_sheet()
        # Pythonic Indexing
        if not isinstance(row, int):
            raise Exception(f"Invalid row identifier of type '{type(row)}'")
        if value in self.listed[row]:
            return [_row[self.listed[row].index(value)] for _row in self.listed]
        return None
    
    @requirements_exists('*')
    def get_dime_by_header(self, value: Union[str, int], header: Union[str, int], refresh: bool = False) -> list[Any]:
        if refresh:
            self.refresh_sheet()
        index = self.get_header_index(header)
        if self.orientation == "vertical":
            for row in self.listed:
                if row[index] == value:
                    return row
            return None
        elif self.orientation == "horizontal":
            if value in self.listed[row]:
                return [_row[self.listed[row].index(value)] for _row in self.listed]
            return None

    @requirements_exists('*')
    def get_header_index(self, header: Union[str, int], refresh: bool = False):
        if refresh:
            self.refresh_sheet()
        if header in self.headers:
            index = self.headers.index(header)
        else:
            raise IdentificationError(f"Header with name '{header}' and depth '{self.header_depth}' in {self.orientation} orientation not found\nHeaders starting with: [{self.headers[0]},...")
        return index # Pythonic Indexing

    @requirements_exists('*')
    def commit_new_row(self, values: Union[list,dict], offset:int=0, refresh=True)->list[gspread.models.Cell]:
        '''
        Parameters:
        - values
            Either a list or dictonary
            A list would be updated in the given order
            A dict would be updated based on the header of the column that corresponds with the dict key
        - offset
            The number of columns to skip from the left before placing the data
            For by headers method, these columns will not be checked
        - refresh
            The nature of this method defaults this parameter to True
        '''
        if refresh:
            self.refresh_sheet()
        new_row_no = len(self.listed)
        old_commits = set(self.commits.copy())
        if isinstance(values,list):
            for i in range(len(values)):
                self.commits.append(gspread.models.Cell(row=new_row_no+1,col=i+1+offset,value=values[i]))
        elif isinstance(values,dict):
            headers = self.headers
            assert headers[offset:]!=[], f'Headers Row Empty (offset={offset})'
            for k,v in values.items():
                if k in headers[offset:]:
                    self.commits.append(gspread.models.Cell(row=new_row_no+1,col=headers[offset:].index(k)+1,value=v))
                else:
                    print(f"Dict key <{k}> could not be found in headers...skipping...")
        return [x for x in set(self.commits) if x not in old_commits]
        
    @requirements_exists('*')
    def commit_new_column(self, values: Union[list,dict], offset:int=0, refresh=True)->list[gspread.models.Cell]:
        '''
        Parameters:
        - values
            Either a list or dictonary
            A list would be updated in the given order
            A dict would be updated based on the header of the column that corresponds with the dict key
        - offset
            The number of columns to skip from the left before placing the data
            For by headers method, these columns will not be checked
        - refresh
            The nature of this method defaults this parameter to True
        '''
        if refresh:
            self.refresh_sheet()
        new_col_no = len(self.listed[0])
        old_commits = set(self.commits.copy())
        if isinstance(values,list):
            for i in range(len(values)):
                self.commits.append(gspread.models.Cell(row=i+1+offset,col=new_col_no+1,value=values[i]))
        elif isinstance(values,dict):
            headers = self.headers
            assert headers[offset:]!=[], f'Headers Column Empty (offset={offset})'
            for k,v in values.items():
                if k in headers[offset:]:
                    self.commits.append(gspread.models.Cell(row=headers[offset:].index(k)+1,col=new_col_no+1,value=v))
                else:
                    print(f"Dict key <{k}> could not be found in headers...skipping...")
        return [x for x in set(self.commits) if x not in old_commits]

    @requirements_exists('*')
    def update_vertical_data(self, data: dict[str,Any], primary_key: str, refresh: bool = False):
        assert isinstance(data,dict), f"data should be type <'dict'> not {type(data)}"
        active_row = self.get_row_by_column(data[primary_key], self.get_header_index(data[primary_key],refresh=refresh),refresh=refresh)
        if active_row == None:
            raise IdentificationError(f'Primary Key ({primary_key}) could not be identified/found')
        active_row_index = self.listed.index(active_row) # Pythonic
        for k,v in data.items():
            if k in self.headers and active_row[self.get_header_index(k,refresh=refresh)]!=v:
                self.commits.append(gspread.models.Cell(row=self.get_header_index(k,refresh=refresh),col=active_row_index,value=v))
                
    def convert_notation(self,value:Union[str,tuple,list]):
        if isinstance(str):
            return gspread.utils.a1_to_rowcol(value)
        elif isinstance(list) or isinstance(tuple):
            return gspread.utils.rowcol_to_a1(value[0],value[1])
        else:
            raise Exception('Invalid Input not A1 Notation or [row,col]')
    
    @requirements_exists('*')
    def delete_row_existence(self, row:int):
        # Row uses Pythonic Indexing
        row += 1
        self.sheet.delete_row(row)
        self.listed = self.sheet.get_all_values()
    
    @requirements_exists('*')
    def delete_col_existence(self,col:int):
        # Col uses Pythonic Indexing
        col += 1 
        self.sheet.delete_col(col)
        self.listed = self.sheet.get_all_values()

    @property
    @requirements_exists('*')
    def headers(self):
        if self.listed != None:
            if getattr(self, 'orientation') == 'vertical':
                return self.listed[self.header_depth-1]
            elif getattr(self, 'orientation') == 'horizontal':
                return [i[self.header_depth-1] for i in self.listed]
