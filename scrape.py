import time
from bs4 import BeautifulSoup
from requests_html import HTMLSession
from urllib.parse import urljoin
import pprint

# Uncomment for the code to work.
# petrinex_pubdata = "https://www.petrinex.gov.ab.ca/PublicData"


def get_all_forms(url):
    """Returns all form tags found on a web page's `url` """
    # GET request
    res = session.get(url)
    # for javascript driven website -> res.html.html will contain the html
    # after javascript execution (render)
    res.html.render()
    soup = BeautifulSoup(res.html.html, "html.parser")
    return soup.find_all("form")


def get_form_details(form):
    """Returns the HTML details of a form,
    including action, method and list of form controls (inputs, etc)"""
    details = {}
    # get the form action (requested URL)
    action = form.attrs.get("action").lower()
    # get the form method (POST, GET, DELETE, etc)
    # if not specified, GET is the default in HTML
    method = form.attrs.get("method", "get").lower()
    # get all form inputs
    inputs = []
    for input_tag in form.find_all("input"):
        # get type of input form control
        input_type = input_tag.attrs.get("type", "text")
        # get name attribute
        input_name = input_tag.attrs.get("name")
        # get the default value of that input tag
        input_value = input_tag.attrs.get("value", "")
        # add everything to that list
        inputs.append({"type": input_type, "name": input_name, "value": input_value})
    # put everything to the resulting dictionary
    details["action"] = action
    details["method"] = method
    details["inputs"] = inputs
    return details


def download_zip_file(s, url, params):
    local_filename = url.split("/")[-1]
    local_filename += ".zip"

    # NOTE the stream=True parameter below
    with s.get(url, stream=True, params=params) as r:
        r.raise_for_status()
        with open(local_filename, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                # If you have chunk encoded response uncomment if
                # and set chunk_size parameter to None.
                # if chunk:
                f.write(chunk)
    return local_filename


# initialize an HTTP session
session = HTMLSession()
res = session.get(petrinex_pubdata)
res.html.render()

# Get the first form from the site
form = get_all_forms(petrinex_pubdata)[0]
form_details = get_form_details(form)

# Prepare data to submit
data = ""
data = {}
for input_tag in form_details["inputs"]:
    nm = input_tag["name"]
    va = input_tag["value"]
    ty = input_tag["type"]
    # Apply our custom logic for the Petrinex form
    if ty == "hidden":
        # if it's hidden, and not one of these use the default value
        if "Download.DownloadCountry" in nm:
            data[nm] = "Canada"
        elif "Download.DownloadIP" in nm:
            data[nm] = "64.146.7.64"  # Need to make this YOUR external IP.
        elif "Download.VolumetricDateFrom" in nm:
            data[nm] = "2017-01-01"
        elif "IsChecked" in nm:
            pass
            # Note the Petrinex site submits each of the checkbox params twice
            # once as true (if checked) and again as false (hidden) no freaking
            # clue whats up with that.  We're just skipping those hidden fields
            # to see if it works
        else:
            data[nm] = va
    elif ty != "submit":
        if nm is not None:
            if "IsChecked" in nm:
                data[nm] = "true"
            elif "FileFormat" in nm:
                data[nm] = "csv"
time.sleep(0.1)

# join the url with the action (form request URL)
# url = urljoin(petrinex_pubdata, form_details["action"])

# work around sillyness with a jquery to get details about
# the requestors ip then resubmitting the form again to
# this url
url = urljoin(petrinex_pubdata, "/PublicData/Files/RequestZipFiles")
session.headers.update(
    {
        "Accept": "content-type: application/json; charset=utf-8",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://www.petrinex.gov.ab.ca",
        "referrer": "https://www.petrinex.gov.ab.ca/PublicData",
        "X-Requested-With": "XMLHttpRequest",
    }
)
res2 = session.post(url, data=data)
json = res2.json()
time.sleep(0.1)

# Now download the actual zip file  - takes 5-10 minutes because we're getting everything.
data = {"arg_strGUID": json["DownloadGUID"]}
url = urljoin(petrinex_pubdata, "/PublicData/Files/DownloadFile")
filename = download_zip_file(session, url, data)
print(filename)

