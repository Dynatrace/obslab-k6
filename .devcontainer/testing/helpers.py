import os, re, subprocess, getpass
from playwright.sync_api import Page, expect, FrameLocator
from loguru import logger
import pytest
import requests
import datetime
import platform

WAIT_TIMEOUT = 10000
SECTION_TYPE_METRICS = "Metrics"
SECTION_TYPE_DQL = "DQL"
SECTION_TYPE_CODE = "Code"
SECTION_TYPE_MARKDOWN = "Markdown"

DT_ENVIRONMENT_ID = os.environ.get("DT_ENVIRONMENT_ID", "")
DT_ENVIRONMENT_TYPE = os.environ.get("DT_ENVIRONMENT_TYPE", "live")
DT_API_TOKEN_TESTING = os.environ.get("DT_API_TOKEN_TESTING", "")
TESTING_DYNATRACE_USER_EMAIL = os.environ.get("TESTING_DYNATRACE_USER_EMAIL", "")
TESTING_DYNATRACE_USER_PASSWORD = os.environ.get("TESTING_DYNATRACE_USER_PASSWORD", "")
REPOSITORY_NAME = os.environ.get("RepositoryName", "")
DEV_MODE = os.environ.get("DEV_MODE", "FALSE").upper() # This is a string. NOT a bool.
CURRENT_USER = getpass.getuser()

TESTING_BASE_DIR = ""
if DEV_MODE == "TRUE":
    TESTING_BASE_DIR = f"./"
else:
    TESTING_BASE_DIR = f"/workspaces/{REPOSITORY_NAME}/.devcontainer/testing"



def get_steps(filename):
    with open(filename, mode="r") as steps_file:
        steps = steps_file.readlines()
        steps_clean = []

        for step in steps:
            step = step.strip()
            steps_clean.append(step)
    
    return steps_clean

# TODO: This assumes env is running on GitHub Codespaces. Improve this
def create_github_issue(output, step_name):
    subprocess.run(["gh", "issue", "create", "--label", "e2e test failed", "--title", f"Failed on step: {step_name}", "--body", f"The end to end test script failed on step: {step_name}\n\n## Output\n```\n{output.stdout}\n```\n\n## stderr \n```\n{output.stderr}\n```"])
    exit(0)

if (
      DT_ENVIRONMENT_ID == "" or
      DT_ENVIRONMENT_TYPE == "" or
      DT_API_TOKEN_TESTING == "" or
      TESTING_DYNATRACE_USER_EMAIL == "" or
      TESTING_DYNATRACE_USER_PASSWORD == ""
   ):
       print("MISSING MANDATORY ENV VARS. EXITING.")
       print(f"DT_ENVIRONMENT_ID: {DT_ENVIRONMENT_ID}")
       print(f"TESTING_DYNATRACE_USER_EMAIL: {TESTING_DYNATRACE_USER_EMAIL}")
       print(f"TESTING_DYNATRACE_USER_PASSWORD: {TESTING_DYNATRACE_USER_PASSWORD}")
       exit()

def login(page: Page):
    page.goto("https://sso.dynatrace.com")
    page.get_by_test_id("text-input").fill(TESTING_DYNATRACE_USER_EMAIL)
    page.wait_for_selector('[data-id="email_submit"]').click()
    page.locator('[data-id="password_login"]').fill(TESTING_DYNATRACE_USER_PASSWORD)
    page.locator('[data-id="sign_in"]').click(timeout=WAIT_TIMEOUT)
    page.wait_for_url("**/ui/**")
    expect(page.locator("title", has_text=DT_ENVIRONMENT_ID).first)

    # Wait for app to load
    wait_for_app_to_load(page)

def open_search_menu(page: Page):
    page.get_by_test_id("dock-search").click()
    expect(page.locator("h1")).to_have_text("Quickly find your apps, documents, entities, and more", timeout=WAIT_TIMEOUT)

def search_for(page: Page, search_term: str):
    page.get_by_label("Search query").fill(search_term)
    expect(page.get_by_label("Result details")).to_be_visible(timeout=WAIT_TIMEOUT)

def open_app_from_search_modal(page: Page, app_name: str):
    page.locator(f"[id='apps:dynatrace.{app_name}']").click()
    page.wait_for_url(f"**/dynatrace.{app_name}/**")
    expect(page).to_have_title(re.compile(app_name, re.IGNORECASE))

    wait_for_app_to_load(page)

def get_app_frame_and_locator(page: Page):
    frame_locator = page.frame_locator('[data-testid="app-iframe"]')
    frame = frame_locator.owner
    return frame_locator, frame

def wait_for_app_to_load(page: Page):
    frame_locator, frame = get_app_frame_and_locator(page)
    expect(frame).to_have_attribute(name="data-isloaded", value="true")
    frame.locator("#content_root").is_visible(timeout=WAIT_TIMEOUT)

    return frame_locator, frame

def create_new_document(page: Page, close_microguide: bool = False):

    wait_for_app_to_load(page)

    app_frame_locator, app_frame = get_app_frame_and_locator(page)

    app_frame_locator.get_by_test_id("new-document-button").first.click()
    expect(app_frame).to_have_attribute(name="data-isloaded", value="true")

    if close_microguide:
        try:
            logger.info("Trying to close the microguide...")
            app_frame.get_by_label("Close microguide").click(timeout=1000)
        except:
            logger.info("Microguide didn't show. That's OK. Proceeding.")

def add_document_section(page, section_type_text):

    wait_for_app_to_load(page)

    app_frame_locator, app_frame = get_app_frame_and_locator(page)

    if section_type_text == SECTION_TYPE_DQL:
        logger.info("Using key combination Shift+D for DQL tile")
        page.keyboard.press("Shift+D")
    elif section_type_text == SECTION_TYPE_CODE:
        logger.info("Using key combination Shift+C for Code tile")
        page.keyboard.press("Shift+C")
    elif section_type_text == SECTION_TYPE_MARKDOWN:
        logger.info("Using key combination Shift+M for Markdown tile")
        page.keyboard.press("Shift+M")
    else:
        page.keyboard.press("ControlOrMeta+Shift+Enter")
        expect(app_frame_locator.get_by_text("Create new section")).to_be_visible(timeout=WAIT_TIMEOUT)
        logger.info(f"Clicking {section_type_text}")
        app_frame_locator.get_by_text(section_type_text, exact=False).first.click(timeout=WAIT_TIMEOUT)

def enter_dql_query(page, dql_query, section_index, validate):

    app_frame_locator, app_frame = get_app_frame_and_locator(page)

    section = app_frame_locator.locator(f"[data-testid-section-index=\"{section_index}\"]")
    
    #section.get_by_label("Enter a DQL query").type(dql_query)
    section.get_by_role("textbox").fill(dql_query)

    if validate:
        validate_document_section_has_data(page, section_index)

def validate_document_section_has_data(page: Page, section_index):

    wait_for_app_to_load(page)
    app_frame_locator, app_frame = get_app_frame_and_locator(page)

    logger.info(f"Validating that section_index {section_index} has data")

    section = app_frame_locator.locator(f"[data-testid-section-index=\"{section_index}\"]")

    # Click the Run button
    section.get_by_test_id("run-query-button").click(timeout=WAIT_TIMEOUT)

    # wait for DQL to finish
    # if this times out, either query took too long
    # of the query was invalid
    try:
        section.get_by_test_id("result-container").wait_for(timeout=WAIT_TIMEOUT)
    except:
        pytest.fail("Either query timed out or an invalid query was provided.")


    # If we get here
    # query executed
    # see if there valid data returned

    # Try to find the "no data" <h6>
    # Remember, NOT finding this is actually a good thing
    # Because then you DO have data
    no_data_heading = section.locator("h6")
    # If the chart graphic does not appear
    # Then the data is not available in Dynatrace
    # and we should error and exit.
    if no_data_heading.is_visible():
        pytest.fail(f"No data found in section_index={section_index}")
    else:
        logger.debug(f"[DEBUG] 1 Data found in section_index={section_index}")

# Specific function to add a metric to a metric type chart
# Note: This does NOT click the "Run query" button
# For data validation, use the valudate_document_section_has_data function
def add_metric(page, search_term, metric_text, section_index, validate):
    
    wait_for_app_to_load(page)
    app_frame_locator, app_frame = get_app_frame_and_locator(page)

    app_frame_locator.get_by_label("Metric key").first.click()

    logger.info(f"Typing `{search_term}` into the box")
    app_frame_locator.get_by_test_id("text-input").fill(search_term)

    app_frame_locator.get_by_label(metric_text).last.click()
    logger.info(f"Selecting {metric_text} from list")    

    # If user has chosen to validate
    # That this metric has data points
    if validate:
        validate_document_section_has_data(page, section_index)


def delete_document(page):
    app_frame_locator, app_frame = get_app_frame_and_locator(page)

    app_frame_locator.get_by_label("Document actions").last.click(timeout=WAIT_TIMEOUT)
    app_frame_locator.get_by_text("Move to trash").last.wait_for(timeout=WAIT_TIMEOUT)
    app_frame_locator.get_by_text("Move to trash").last.click(timeout=WAIT_TIMEOUT)

# This function takes a snippet name
# and retrieves the DQL using runme
# eg. { "name": "fetch events dql"}
def retrieve_dql_query(snippet_name):
    output = subprocess.run(["runme", "print", snippet_name], capture_output=True, text=True)
    # Spit the output and keep the newline characters
    lines = output.stdout.splitlines(keepends=True)
    
    snippet = ""
    current_position = 0
    for line in lines:
        # First line is always
        # ``` {"name": "****"}
        # So ignore it always
        if current_position == 0:
            current_position += 1
            continue

        # If the line starts with backticks
        # We know it's the final useful line
        # So immediately exit
        if line.startswith("```"):
            break

        # If here
        # Every other line is useful
        # So append to the snippet
        # Increment position counter to ensure we get all lines
        snippet += line
        current_position += 1
    return snippet

def build_dt_urls(dt_env_id, dt_env_type="live"):
    if dt_env_type.lower() == "live":
        dt_tenant_apps = f"https://{dt_env_id}.apps.dynatrace.com"
        dt_tenant_live = f"https://{dt_env_id}.live.dynatrace.com"
    else:
      dt_tenant_apps = f"https://{dt_env_id}.{dt_env_type}.apps.dynatrace.com"
      dt_tenant_live = f"https://{dt_env_id}.{dt_env_type}.dynatrace.com"

    # if environment is "dev" or "sprint"
    # ".dynatracelabs.com" not ".dynatrace.com"
    if dt_env_type.lower() == "dev" or dt_env_type.lower() == "sprint":
        dt_tenant_apps = dt_tenant_apps.replace(".dynatrace.com", ".dynatracelabs.com")
        dt_tenant_live = dt_tenant_live.replace(".dynatrace.com", ".dynatracelabs.com")
    
    return dt_tenant_apps, dt_tenant_live

def create_dt_api_token(token_name, scopes, dt_rw_api_token, dt_tenant_live):

    # Automatically expire tokens 1 hour in future.
    time_future = datetime.datetime.now() + datetime.timedelta(hours=1)
    expiry_date = time_future.strftime("%Y-%m-%dT%H:%M:%S.999Z")

    headers = {
        "accept": "application/json; charset=utf-8",
        "content-type": "application/json; charset=utf-8",
        "authorization": f"api-token {dt_rw_api_token}"
    }

    payload = {
        "name": token_name,
        "scopes": scopes,
        "expirationDate": expiry_date
    }

    resp = requests.post(
        url=f"{dt_tenant_live}/api/v2/apiTokens",
        headers=headers,
        json=payload
    )

    if resp.status_code != 201:
        exit(f"Cannot create DT API token: {token_name}. Response was: {resp.status_code}. {resp.text}. Exiting.")

    return resp.json()['token']

# Set a system-wide environment variable
# Defaults to bash shell but can be overriden
def store_env_var(key, value):
    with open(file=".env", mode="a") as env_file:
        env_file.write(f"{key}={value}\n")