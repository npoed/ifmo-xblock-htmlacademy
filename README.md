# ifmo-xblock-htmlacademy

## Installation

Add following parameters in `lms.env.json`:

```javascript
"XBLOCK_SETTINGS": {
    "IFMO_XBLOCK_HTMLACADEMY": {
        "SELECTED_CONFIGURATION": "selected_configuration"
        "LAB_URL": "lab_url_goes_here",
        "API_URL": "api_url_goes_here",
        "SECRET": "secret_goes_here"
    }
}
```

`SELECTED_CONFIGURATION` can now be `ifmo`, `npoed` or `default`.

`LAB_URL` is optional, may be omitted when `SELECTED_CONFIGURATION` is either 
`ifmo` or `npoed` otherwise unpredicted behaviour may occur.

`API_URL` is optional, may be omitted when `SELECTED_CONFIGURATION` is either 
`ifmo` or `npoed` otherwise unpredicted behaviour may occur.

`SECRET` is required, provided by HTML Academy service.

Sample for `server_vars.yml`:

```yml
XBLOCK_SETTINGS:
    IFMO_XBLOCK_HTMLACADEMY:
        SELECTED_CONFIGURATION: "selected_configuration_goes_here"
        LAB_URL: "lab_url_goes_here"
        API_URL: "api_url_goes_here"
        SECRET: "secret_goes_here"
```
