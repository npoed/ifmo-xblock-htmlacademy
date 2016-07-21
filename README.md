# ifmo-xblock-htmlacademy

XBlock for edx-platfrom implementing interconnection between Open edX and HTML Academy.

## Requirements

Add the following line in `requirements.txt`:

```
-e git+https://github.com/openeduITMO/ifmo-xblock-htmlacademy@v4.1#egg=ifmo-xblock-htmlacademy==4.1
```

## Installation

Add following parameters in `lms.env.json`:

```javascript
"XBLOCK_SETTINGS": {
    "IFMO_XBLOCK_HTMLACADEMY": {
        "SELECTED_CONFIGURATION": "selected_configuration",
        "LAB_URL": "lab_url_goes_here",
        "API_URL": "api_url_goes_here",
        "SECRET": "secret_goes_here"
    }
}
```

Add following apps in `INSTALLED_APPS`:

```python
INSTALLED_APPS += (
    "xblock_htmlacademy",
)
```

Or modify `lms.env.json` and `cms.env.json`:
 
```javascript
"ADDL_INSTALLED_APPS": [
    "xblock_htmlacademy"
]
```

## Configuration

`SELECTED_CONFIGURATION` can now be `ifmo`, `npoed` or `default`.

`LAB_URL` is optional, may be omitted when `SELECTED_CONFIGURATION` is either 
`ifmo` or `npoed` otherwise unpredicted behaviour may occur.

`API_URL` is optional, may be omitted when `SELECTED_CONFIGURATION` is either 
`ifmo` or `npoed` otherwise unpredicted behaviour may occur.

`SECRET` is required, provided by HTML Academy service.

## Deployment

Sample for `server_vars.yml`:

```yml
XBLOCK_SETTINGS:
    IFMO_XBLOCK_HTMLACADEMY:
        SELECTED_CONFIGURATION: "selected_configuration_goes_here"
        LAB_URL: "lab_url_goes_here"
        API_URL: "api_url_goes_here"
        SECRET: "secret_goes_here"
```

## Usage

XBlock provides entry point `xblock_htmlacademy` which must be used in course **Advanced settings**.
