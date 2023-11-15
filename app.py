import json
import os
from typing import Tuple
import gspread
import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

cp_to_link = {
    "Checkpoint 1" : st.secrets['private_url_cp1'],
    "Checkpoint 2" : st.secrets['private_url_cp2']
}

st.set_page_config(page_title='Checkpoint viewer', page_icon='logo.png')
add_selectbox = st.sidebar.selectbox(
    "Choose checkpoint",
    ("Checkpoint 1", "Checkpoint 2")
)
# print(add_selectbox)


with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)

authenticator.login('Login', 'main')

EXCLUDED_FIELDS = [
    'Отметка времени', 'Группа'
]

if not os.path.exists('feedback.json'):
        with open('feedback.json', 'w') as f:
            json.dump(dict(st.secrets['gcp_service_account']), f, default=dict)

gc = gspread.service_account(
    filename="feedback.json",
    scopes=[
        "https://www.googleapis.com/auth/spreadsheets",
    ]
    )

# @st.cache_resource
def get_table() -> gspread.spreadsheet.Spreadsheet:
    """
    Returns:
        gspread.spreadsheet.Spreadsheet
    """
    if gc: 
        # tables = gc.open_by_url(st.secrets["private_gsheets_url"])
        print(cp_to_link[add_selectbox])
        tables = gc.open_by_url(cp_to_link[add_selectbox])
    return tables


def get_worksheet(group_name: str, n: int = 0) -> Tuple[pd.DataFrame, list]: 
    """Get page from google sheet

    Args:
        n (int, optional): List number. Defaults to 0.
        group_name (str, optional): Team (should be selected in radio group).

    Returns:
        Tuple[pd.DataFrame, list]: answers dataframe and question list
    """
    table = get_table()
    worksheet = pd.DataFrame(table.get_worksheet(n).get_all_records())
    subset = worksheet[worksheet['Группа'] == group_name]\
        .drop(['Отметка времени', 'Группа'], axis=1)
    questions = subset.columns.tolist()
    return subset, questions

def load_answers(load: any, group: any) -> None: 
    """Rendering the page after a button is clicked

    Args:
        load (any): any but not None 
        group (any): any but not None
    """
    df, questions = get_worksheet(group_name=group, n=0)

    for ix, q in enumerate(questions):
        st.markdown(f'#### {ix+1}. {q}')
        for a in df[q].tolist():
            st.markdown(f'* {a}')

if __name__ == "__main__":
    if st.session_state["authentication_status"]:
        cols = st.columns(4, gap='large')
        with cols[0]:
            # show groups if logged in
            group = st.radio("Группа", ["Satellite", "Sirius", "Meteors", "Asteroids", "Comets"])
            load = st.button('Load answers')
        with cols[-1]:
            # make logout button
            authenticator.logout('Logout', 'main', key='unique_key')
        if load and group:
                load_answers(load, group)
    elif st.session_state["authentication_status"] is False:
        st.error('Username/password is incorrect')
    elif st.session_state["authentication_status"] is None:
        st.warning('Please enter your username and password')
    

