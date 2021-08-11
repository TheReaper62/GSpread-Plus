from distutils.core import setup
setup(
    name = 'GSpreadPlus',
    packages = ['GSpreadPlus'],
    version = '0.2',
    license='MIT',
    description = 'Specific Use Cases for Gspread Wrapper',
    author = 'FishballNoodles',
    author_email = 'joelkhorxw@gmail.com',
    url = 'https://github.com/TheReaper62/GSpread-Plus',
    download_url = 'https://github.com/TheReaper62/GSpread-Plus/archive/refs/tags/v0.2.tar.gz',
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
    long_description = "Made on top of the orginal gspread Python API Wrapper, this wrapper (wrapper of a wrapper) targets at specific use cases such as returning row after finding column for a value. You'll get it if you use it. Development is open source and you can also request for features by opening an issue in Github."
)
