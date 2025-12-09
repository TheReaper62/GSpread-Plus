'''
GSpreadPlus: A GSpread Wrapper of a Google Sheets API Wrapper
Description:
This module provides a high-level interface for interacting with Google Sheets as a database
Author: Joel Khor
License: MIT License
'''

from __future__ import annotations
from typing import Union, Optional, Callable, Any

from oauth2client.service_account import ServiceAccountCredentials
import gspread

from .errors import IdentificationError, SetupError

__all__ = (
    'Spreadclient',
)

def requirements_exists(*requirements):
    '''Decorator to check if object has requirements'''
    def decorator(func):
        def wrapper(*args, **kwargs):
            nonlocal requirements
            if requirements[0] == '*':
                requirements = ['client','document','sheet']
            if args[0].client is None and 'client' in requirements:
                raise SetupError("Client has not been initialised")
            if args[0].document is None and 'document' in requirements:
                raise SetupError("Document has not been connected")
            if args[0].sheet is None and 'sheet' in requirements:
                raise SetupError("Sheet within document has not been connected")
            return func(*args,**kwargs)
        return wrapper
    return decorator

class Spreadclient:
    '''The base GSpreadPlus Client to interact with Google Sheets'''
    def __init__(self, credentials: Union[str,dict[str,str]]):
        scopes = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
        # Name of Credentials File (.json)
        if isinstance(credentials,str):
            creds = ServiceAccountCredentials.from_json_keyfile_name(credentials, scopes)
        # Dictionary of Credentials
        elif isinstance(credentials,dict):
            creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials, scopes)
        else:
            raise SetupError(f"Invalid Credentials of type '{type(credentials)}'")
        self.client = gspread.authorize(creds)
        self.document = None
        self.sheet = None
        self.listed = None
        self.verlisted = None
        self.commits = []
        self.orientation = None
        self.header_depth = None


    @requirements_exists('client')
    def connect_document(self, identifier):
        '''Connect to a Google Sheets Document by key, name or url'''
        methods = [self.client.open_by_key,self.client.open,self.client.open_by_url]
        for method in methods:
            self.document = method(identifier)
            if self.document is not None:
                break
        else:
            raise IdentificationError(
                f"Document identifier <{identifier}> did not fit one of the formats (key,name,url)"
            )

        self.listed = None
        self.verlisted = None
        self.sheet = None
        self.commits = []
        self.orientation = None
        self.header_depth = None

    @requirements_exists('client','document')
    def connect_sheet(
        self, identifier: str="Sheet1", orientation: str='vertical', header_depth: int=1
    ) -> None:
        '''Connect to sheet within the connected document by name or index'''
        if isinstance(identifier,str):
            self.sheet = self.document.worksheet(identifier)
            identifier = f"Name '{identifier}'"
        elif isinstance(identifier,int):
            self.sheet = self.document.get_worksheet(identifier)
            identifier = f"Index < {identifier} >"

        self.orientation = orientation
        self.header_depth = header_depth

        if self.sheet is None:
            raise IdentificationError(f"Sheet with the {identifier} Not Found")
        else:
            # Intialize listed on sheet connection
            self.refresh_sheet()

    @requirements_exists('*')
    def refresh_sheet(self):
        '''Update local cache of changes and fetch latest data from sheet'''
        if len(self.commits) > 0:
            self.sheet.update_cells(self.commits)
            self.commits = []
        self.listed = self.sheet.get_all_values()
        self.verlisted = list(map(list, zip(*self.listed)))

    @requirements_exists('*')
    def get_row_by_column(
        self, value: Union[str,int], column: Union[str, int]=0, refresh: bool=False
    ) -> list[Any]:
        '''Get the first row that matches the value in the specified column'''
        if refresh:
            self.refresh_sheet()
        # Pythonic Indexing
        if isinstance(column, str) and column.isalpha():
            index = gspread.utils.a1_to_rowcol(f"{column.upper()}1")[0] - 1
        elif isinstance(column, int):
            index = column
        else:
            raise TypeError(f"Invalid Column identifier of type '{type(column)}'")
        for row in self.listed:
            if row[index] == value:
                return row
        return None

    @requirements_exists('*')
    def get_rows_by_func(self, function: Callable, refresh: bool=False) -> list[Any]:
        '''Get all rows that match the condition specified in the function'''
        if refresh:
            self.refresh_sheet()
        match = []
        for row in self.listed:
            if function(row):
                match.append(row)
        return match

    @requirements_exists('*')
    def get_column_by_row(
        self, value: Union[str, int], row: int=0, refresh: bool=False
    ) -> list[Any]:
        '''Get the first column that matches the value in the specified row'''
        if refresh:
            self.refresh_sheet()
        # Pythonic Indexing
        if not isinstance(row, int):
            raise TypeError(f"Invalid row identifier of type '{type(row)}'")
        if value in self.listed[row]:
            return [_row[self.listed[row].index(value)] for _row in self.listed]
        return None

    @requirements_exists('*')
    def get_dime_by_header(
        self, value: Union[str, int], header: Union[str, int], refresh: bool=False
    ) -> Optional[list[Any]]:
        '''Get the first row/column that matches the value in the specified header'''
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
    def get_header_index(self, header: Union[str, int], refresh: bool = False) -> int:
        '''Get the index of the specified header'''
        if refresh:
            self.refresh_sheet()
        if header in self.headers:
            index = self.headers.index(header)
        else:
            raise IdentificationError(
                f"Header with name '{header}', depth '{self.header_depth}' in {self.orientation} "
                f"orientation not found\nHeaders starting with: [{self.headers[0]},..."
            )
        return index # Pythonic Indexing

    @requirements_exists('*')
    def commit_new_row(
        self, values: Union[list,tuple,dict], offset: int=0, refresh: bool=True
    ) -> list[gspread.cell.Cell]:
        '''
        Parameters:
        - values
            Either a list, tuple or dictonary
            A list would be updated in the given order
            A dict would be updated based on the header of the column that corresponds with each key
        - offset
            The number of columns to skip from the left before placing the data
            For by headers method(dict), these columns will not be checked
        - refresh
            The nature of this method defaults this parameter to True
        '''
        if refresh:
            self.refresh_sheet()
        new_row_no = len(self.listed)
        old_commits = set(self.commits.copy())
        if isinstance(values,(list, tuple)):
            for k,v in enumerate(values):
                self.commits.append(gspread.cell.Cell(row=new_row_no+1,col=k+1+offset,value=v))
        elif isinstance(values,dict):
            headers = self.headers
            assert headers[offset:]!=[], f'Headers Row Empty (offset={offset})'
            for k,v in values.items():
                if k in headers[offset:]:
                    self.commits.append(
                        gspread.cell.Cell(row=new_row_no+1,col=headers[offset:].index(k)+1,value=v)
                    )
                else:
                    print(f"Dict key <{k}> could not be found in headers...skipping...")
        return [x for x in [
            i for i in self.commits if self.commits.count(x)>1
        ] if x not in old_commits]

    @requirements_exists('*')
    def commit_new_multiple_rows(
        self, values: Union[list[list],list[dict]], offset: int=0, refresh: bool=True
    ) -> list[gspread.cell.Cell]:
        '''
        Parameters:
        - values
            A list of either a list, tuple or dictonary
            A list would be updated in the given order
            A dict would be updated based on the header of the column that corresponds with each key
        - offset
            The number of columns to skip from the left before placing the data
            For by headers method(dict), these columns will not be checked
        - refresh
            The nature of this method defaults this parameter to True
        '''
        if refresh:
            self.refresh_sheet()
        new_row_no = len(self.listed)
        old_commits = set(self.commits.copy())
        internal_offset = 0
        if isinstance(values[0],(list, tuple)):
            for item in values:
                for k,v in enumerate(item):
                    self.commits.append(
                        gspread.cell.Cell(row=new_row_no+internal_offset+1,col=k+1+offset,value=v)
                    )
                internal_offset += 1
        elif isinstance(values[0],dict):
            headers = self.headers
            assert headers[offset:]!=[], f'Headers Row Empty (offset={offset})'
            for item in values:
                for k,v in item.items():
                    if k in headers[offset:]:
                        self.commits.append(gspread.cell.Cell(
                            row=new_row_no+internal_offset+1,
                            col=headers[offset:].index(k)+1,
                            value=v
                        ))
                    else:
                        print(f"Dict key <{k}> could not be found in headers...skipping...")
                internal_offset += 1
        if refresh:
            self.refresh_sheet()
        relevant_commits = [i for i in self.commits if self.commits.count(i)>1]
        return [x for x in relevant_commits if x not in old_commits]

    @requirements_exists('*')
    def commit_new_column(
        self, values: Union[list,tuple,dict], offset: int=0, refresh: bool=True
    ) -> list[gspread.cell.Cell]:
        '''
        Parameters:
        - values
            Either a list, tuple or dictonary
            A list would be updated in the given order
            A dict would be updated based on the header of the column that corresponds with each key
        - offset
            The number of columns to skip from the left before placing the data
            For by headers method(dict), these columns will not be checked
        - refresh
            The nature of this method defaults this parameter to True
        '''
        if refresh:
            self.refresh_sheet()
        new_col_no = len(self.listed[0])
        old_commits = set(self.commits.copy())
        if isinstance(values,(list, tuple)):
            for k,v in enumerate(values):
                self.commits.append(
                    gspread.cell.Cell(row=k+1+offset,col=new_col_no+1,value=v)
                )
        elif isinstance(values,dict):
            headers = self.headers
            assert headers[offset:]!=[], f'Headers Column Empty (offset={offset})'
            for k,v in values.items():
                if k in headers[offset:]:
                    self.commits.append(
                        gspread.cell.Cell(row=headers[offset:].index(k)+1,col=new_col_no+1,value=v)
                    )
                else:
                    print(f"Dict key <{k}> could not be found in headers...skipping...")
        return [x for x in set(self.commits) if x not in old_commits]

    @requirements_exists('*')
    def update_vertical_data(self, data: dict[str,Any], primary_key: str, refresh: bool=False):
        '''Refreshes and updates a column based on the primary key provided'''
        assert isinstance(data,dict), f"data should be type <'dict'> not {type(data)}"
        active_row = self.get_row_by_column(
            data[primary_key], self.get_header_index(primary_key,refresh=refresh), refresh=refresh
        )
        if active_row is None:
            raise IdentificationError(f'Primary Key ({primary_key}) could not be identified/found')
        active_row_index = self.listed.index(active_row) # Pythonic
        for k,v in data.items():
            if k in self.headers and active_row[self.get_header_index(k,refresh=refresh)]!=v:
                self.commits.append(gspread.cell.Cell(
                    col=self.get_header_index(k,refresh=refresh)+1,row=active_row_index+1,value=v
                ))

    def convert_notation(self, value: Union[str,tuple,list]):
        '''Util to convert between A1 Notation and [row,col] Notation'''
        if isinstance(value, str):
            return gspread.utils.a1_to_rowcol(value)
        elif isinstance(value, list) or isinstance(value, tuple):
            return gspread.utils.rowcol_to_a1(value[0],value[1])
        else:
            raise TypeError(f"Invalid Input <{value}> not A1 Notation or [row,col]")

    @requirements_exists('*')
    def delete_rows(self, rows: Union[int, list[int], tuple[int,int]]) -> None:
        '''Delete (not clear) a row(s) from the sheet'''
        # Row uses Pythonic Indexing
        if isinstance(rows, int):
            rows += 1
            self.sheet.delete_rows(rows)
        elif isinstance(rows,(list,tuple)):
            self.sheet.delete_rows(*rows)
        self.listed = self.sheet.get_all_values()

    @requirements_exists('*')
    def delete_columns(self, cols: Union[int, list[int], tuple[int,int]]) -> None:
        '''Delete (not clear) a column from the sheet'''
        # Col uses Pythonic Indexing
        if isinstance(cols, int):
            cols += 1
            self.sheet.delete_columns(cols)
        elif isinstance(cols,(list,tuple)):
            self.sheet.delete_columns(*cols)
        self.listed = self.sheet.get_all_values()

    @property
    @requirements_exists('*')
    def headers(self):
        '''Get the headers considering orientation and header depth'''
        if self.listed is not None:
            if getattr(self, 'orientation') == 'vertical':
                return self.listed[self.header_depth-1]
            elif getattr(self, 'orientation') == 'horizontal':
                return [i[self.header_depth-1] for i in self.listed]
