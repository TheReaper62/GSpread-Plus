from distutils.core import setup
setup(
    name = 'GSpreadPlus',
    packages = ['GSpreadPlus'],
    version = '0.1',
    license='MIT',
    description = 'Specific Use Cases for Gspread Wrapper',
    author = 'FishballNoodles',
    author_email = 'joelkhorxw@gmail.com',
    url = 'https://github.com/TheReaper62/GSpread-Plus',
    download_url = 'https://github.com/user/reponame/archive/v_01.tar.gz',
    keywords = ['Google Spreadsheets', 'Sheets', 'Sheetsv4','Python 3+','google-spreadsheets','spreadsheets'],
    install_requires= [
        'oauth2client',
        'gspread'
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
)
