# GSpreadPlus - Google Spreadsheets GSpreadPlus
****
Made on top of the orginal gspread Python API Wrapper, this wrapper (wrapper of a wrapper) targets at specific use cases such as returning row after finding column for a value. You'll get it if you use it.

# Installation
****
### Using PIP
**Windows** - `Command Prompt`:
```shell
python -m pip install GSpreadPlus
```
OR

**Linux/MacOs** - `Terminal`
```shell
python3 -m pip install GSpreadPlus
```
Done!!!
#
## Project Status
 + ~~Alpha~~ **Beta**
 + Open Source
#
# Tutorial
## 1. Import & Initializing
Import:
```py
from GSpreadPlus import Spreadclient
```
Intialising:
```py
client = Spreadclient('credentials.json')
```
OR
```py
from json import loads
creds = loads('credentials.json')
client = Spreadclient(creds)
```
#
## 2. Connecting to Document/Sheet
To connect to the document, you need either one of the following Identifiers:
- Document **Name**
- Document **Unique ID** (Can be found in URL)
- Document **URL**

Connecting to **Document**:
```py
client.connect_document('Banana Sales')
# OR
client.connect_document('4n5Dk5nfSxW1kNKG6vjZOAulDKgMb7JgcKEVlJb4mMpY')
# OR
client.connect_document('https://docs.google.com/spreadsheets/d/4n5Dk5nfSxW1kNKG6vjZOAulDKgMb7JgcKEVlJb4mMpY')
```
Connecting to **Worksheet**:
- By **Name**
- By **Index** *(Pythonic)*
```py
client.connect_sheet('Monkey Employees')
# OR
client.connect_sheet(0)
```
***Extra Attributes for Databases:***
1. Orientation - `orientation`
    - If you are treating the spreadsheet like a database, you can set the `orientation` to either `'vertical'`*(default)* or `'horizontal'`
    - This will automatically get the headers depending on the orientation
    - If the data is propagating `vertical`ly, that would be the orientation
;
2. Headers Depth - `headers_depth`
    - If your databases have headers that are not starting from the first row/column you can change the depth
    - For example if your headers are at row 3, the headers depth would be `3`
```py
client.connect_sheet(
    'Monkey Employees',
    orientation='horizontal',
    headers_depth=3
)
```
#
## 3. Reading Data
Accessing the `listed` and `headers` attribute will gain access to their respective properties.

`listed` returns a list of list, where each list represents a row and each element in the inner list represents a cell

`headers` returns the headers based on the `orientation`

### Refreshing:
Refreshing the data will send a request to the server for the new data and will push new local commits(changes).

Do note that refreshing will overwrite `listed` and it will overwrite the live spreadsheet regardless of its state.

In essence, we are assuming the live spreadsheet data doesn't get changed between the last fetched data and that instance.
```py
client.refresh_sheet()

data = client.listed
print(f"There are {len(data)} rows in this sheet")

headers = client.headers
print(f"This spreadsheets' headers: {headers}")
```
> Do note that `client.refresh_sheet()` should be used sparingly in order to reduce requests sent to the server and ultimately avoiding `TOO_MANY_REQUESTS`
#
## 4. Querying Data
Since this package is for sheets that work/act as databases, the following functions exist to assist in such tasks

>### Included Refreshing
>For ALL query functions, and optional parameter `refresh=False` is available.
>
>When set to `True`, `self.refresh_sheet()` will be invoked before executing the relevant function

******
### A. Get Row by Column
`get_row_by_column(self, value: Union[str, int], column: Union[str, int] = 0, refresh: bool = False)->list[Any]`
### Parameters
- `value: Union[str, int]`
    - This is the value that will be searched.
    - Returns a list of element for the first row that `<column>` matches `value` (case-sensitive)
- `column: Union[str, int]`
    - This is the column that `value` will be searched in
    - `column` can be column name (e.g. `'A'`) or index *(Pythonic, e.g. `0`)*
****
### B. Get Dimension by Header Name
`get_dime_by_header(self, value: Union[str,int], header: Union[str, int], refresh: bool = False)->list[Any]`
### Parameters
- `value: Union[str, int]`
    - This is the value that will be searched.
    - Returns a list of element for the first row/column that `<header attribute>` matches `value` (case-sensitive)
- `header: Union[str, int]`
    - This is the `header` for the column that `value` will be searched in
    - `header` is **case-sensitive**
****
### C. Get Rows by Function
`get_rows_by_func(self, function: Callable, refresh: bool = False)->list[Any]`
### Parameters
- `function: Callable`
    - `function` should accept 1 parameter which is the `row` (i.e. list of cells in each row)
    - Should return a `boolean` value
```py
matches = client.get_rows_by_func(
    lambda r:'pizza' in r[
            client.get_header_index('Fav Food')
        ].lower(),
    refresh = True
)
```
****
### D. Commit/Add New Row
`commit_new_row(self, values: Union[list,dict], offset:int=0, refresh=True)->list[gspread.models.Cell]`
### Parameters
- `values: Union[list,dict]`
    - Add new row of values based on dict keys or just by listical order
    - If `refresh=False`, the update will NOT be LIVE until `refresh_sheet()` is called again.

> Returns list of Cells that have been added to `self.commits`
