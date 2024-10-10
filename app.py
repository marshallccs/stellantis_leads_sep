import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, ColumnsAutoSizeMode, GridOptionsBuilder
from st_data_explore import get_data, get_metrics
import plotly.express as px
import numpy as np
import hmac

def check_password():

   """Returns `True` if the user had the correct password."""
   def password_entered():

       """Checks whether a password entered by the user is correct."""

       if hmac.compare_digest(st.session_state["password"], st.secrets["password"]):
           st.session_state["password_correct"] = True
           del st.session_state["password"]  # Don't store the password.
       else:
           st.session_state["password_correct"] = False

   # Return True if the password is validated.
   if st.session_state.get("password_correct", False):
       return True
   # Show input for password.
   st.text_input(
       "Password", type="password", on_change=password_entered, key="password"
   )
   if "password_correct" in st.session_state:
       st.error("😕 Password incorrect")
   return False

if not check_password():
   st.stop()  # Do not continue if check_password is not True.



#set page
st.set_page_config(page_title="2024 Reporting", page_icon="🌎", layout="wide")

# Set page header
st.image('Stellantis-Logo.png', width=300)
st.header('Leads January - May 2024', divider='blue')
st.markdown('')

df = get_data()

# Select all option
def av_options(df, options):
    available_options = df[options].unique().tolist()
    available_options.insert(0, -1)

    if "max_selections" not in st.session_state:
        st.session_state["max_selections"] = len(available_options)

    return available_options


def options_select(available_options, selected_options):
    if selected_options in st.session_state:
        if -1 in st.session_state[selected_options]:
            st.session_state[selected_options] = available_options[1:]
            st.session_state["max_selections"] = len(available_options)
        else:
            st.session_state["max_selections"] = len(available_options)


def multi_select_filters(df):
    df['DTcreated'] = pd.to_datetime(df['DTcreated'])
    min_date = df['DTcreated'].min()
    max_date = df['DTcreated'].max()

    st.markdown('Filter the start and end period for the report')
    date_col1, date_col2 = st.columns(2)
    with date_col1:
        start_date = st.date_input('Start Date', value=min_date, min_value=min_date, max_value=max_date)
    with date_col2:
        end_date = st.date_input('End Date', value=max_date, min_value=min_date, max_value=max_date)

    df_selection = df.query(
        "DTcreated>=@start_date & DTcreated<=@end_date"
    )

    st.checkbox('Filter by Dealer and Brand', key='show_filter')
    if st.session_state.show_filter:
        dealer = st.multiselect(
            label='Filter Dealer',
            options=av_options(df, 'Dealer'),
            default=av_options(df, 'Dealer')[1:],
            key='dealer_options',
            on_change=options_select(av_options(df, 'Dealer'), 'dealer_options'),
            format_func=lambda x: 'All' if x == -1 else f'{x}',
        )

        brand = st.multiselect(
            label='Filter Dealer',
            options=av_options(df, 'InterestMake'),
            default=av_options(df, 'InterestMake')[1:],
            key='interestmake_options',
            on_change=options_select(av_options(df, 'InterestMake'), 'interestmake_options'),
            format_func=lambda x: 'All' if x == -1 else f'{x}',
        )

        df_selection = df.query(
            "Dealer==@dealer & DTcreated>=@start_date & DTcreated<=@end_date & InterestMake==@brand"
        )

    return df_selection

def metrics(df):
    from streamlit_extras.metric_cards import style_metric_cards
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(label="Total Leads", value=df['InterestMake'].count(), delta="")
    col2.metric(label="Active Leads", value=get_metrics(df, 'Active Leads'), delta="")
    col3.metric(label="Lost Leads", value=get_metrics(df, 'Lost Leads'), delta="")
    col4.metric(label="Sold Leads", value=get_metrics(df, "Sold Leads"), delta="")
    style_metric_cards(background_color="#FFFFFF", border_left_color="#0F5290")


def lead_status_pie(df):
    col1, col2 = st.columns(2)
    status_df = pd.DataFrame(df.groupby('StatusCheck')['StatusCheck'].value_counts()).reset_index()
    stat_pie = px.pie(status_df, values='count', names='StatusCheck', title="Lead Per Category")
    stat_pie.update_layout(title_x=0.42, legend_orientation='h', legend_indentation=100)

    lead_df = pd.DataFrame(df.groupby('LeadStatus')['LeadStatus'].value_counts()).reset_index()
    lead_pie = px.pie(lead_df, values='count', names='LeadStatus', title="Leads Per Status")
    lead_pie.update_layout(title_x=0.42, legend_orientation='h', legend_indentation=20)

    with col1:
        container1 = st.container(border=True)
        container1.plotly_chart(stat_pie, use_container_width=True, theme='streamlit')
    with col2:
        container2 = st.container(border=True)
        container2.plotly_chart(lead_pie, use_container_width=True, theme='streamlit')

def leads_per_source(df):
    # TODO: Take the same approach as the brand section to get the value formatted properly. Add a total row column
    leads_ps = df.pivot_table(values='CallCentreStatus', index=['LeadSource', 'StatusCheck'], aggfunc=np.count_nonzero)
    leads_ps = pd.DataFrame(leads_ps).reset_index()
    summary = pd.DataFrame(leads_ps.groupby('LeadSource')['CallCentreStatus'].sum()).reset_index()
    summary['StatusCheck'] = 'Total'
    leads_ps = pd.concat([leads_ps, summary], ignore_index=True)
    leads_list = leads_ps['LeadSource'].unique().tolist()
    ld_list = []

    for source in leads_list:
        source_df = leads_ps.loc[leads_ps['LeadSource'] == source].copy()
        status_list = source_df['StatusCheck'].unique().tolist()
        status_list.sort()
        ele = status_list.pop()
        for status in status_list:
            status_df = source_df.loc[source_df['StatusCheck'] == status].copy()
            total_df = source_df.loc[source_df['StatusCheck'] == 'Total'].copy()
            f_value = status_df['CallCentreStatus'].sum()
            total = total_df['CallCentreStatus'].sum()
            percent = round((f_value / total) * 100, 2)
            
            result_obj = {
                'LeadSource': [source],
                'StatusCheck': [f'{status} %'],
                'CallCentreStatus': [percent],
            }
            result_df = pd.DataFrame(result_obj)
            ld_list.append(result_df)
    
    percent_df = pd.concat(ld_list, ignore_index=True)
    leads_ps = pd.concat([leads_ps, percent_df], ignore_index=True)



    gb = GridOptionsBuilder()

    gb.configure_default_column(
        resizable=True,
        filterable=True,
        sortable=True,
        editable=False
    )
    gb.configure_column(field='LeadSource', header_name='Lead Source', width=80, rowGroup=True)

    gb.configure_column(
        field='StatusCheck',
        header_name='Total',
        pivot=True
    )
    gb.configure_column(
        field='CallCentreStatus',
        header_name='Total',
        aggFunc='sum',
        valueFormatter="value.toLocaleString()",
    )
    gb.configure_grid_options(
        tooltipShowDelay=0,
        pivotMode=True,
        suppressAggFuncInHeader=True,
        grandTotalRow='bottom'
    )
    gb.configure_grid_options(
        autoGroupColumnDef=dict(
            minWidth=300,
            pinned='left',
            cellRendererParams=dict(suppressCount=True)
        )
    )

    go = gb.build()
    AgGrid(leads_ps, gridOptions=go, height=400, fit_columns_on_grid_load=ColumnsAutoSizeMode.FIT_CONTENTS)
    # st.dataframe(percent_df)


def lead_per_source_per_brand(df):
    # TODO: Try to use the valueGetter to add in the percentage columns.
    # TODO: If valueGetter works, try to rearrange the table if needed.
    new_df = df.copy()
    lead_df = new_df.pivot_table(values='CallCentreStatus', index=['InterestMake', 'LeadSource', 'StatusCheck'], aggfunc=np.count_nonzero)
    lead_df = pd.DataFrame(lead_df).reset_index()
    summary = pd.DataFrame(lead_df.groupby(['InterestMake', 'LeadSource'])['CallCentreStatus'].sum()).reset_index()
    summary['StatusCheck'] = 'Total'
    lead_df = pd.concat([lead_df, summary], ignore_index=True)

    gb = GridOptionsBuilder()

    gb.configure_default_column(
        resizable=True,
        filterable=True,
        sortable=True,
        editable=False
    )
    gb.configure_column(field='InterestMake', header_name='Brand', width=80, rowGroup=True)
    gb.configure_column(field='LeadSource', header_name='Brand', width=80, rowGroup=True)

    gb.configure_column(
        field='StatusCheck',
        header_name='Total',
        pivot=True
    )
    gb.configure_column(
        field='CallCentreStatus',
        header_name='Total',
        aggFunc='sum',
        valueFormatter='value.toLocaleString()',
    )
    gb.configure_grid_options(
        tooltipShowDelay=0,
        pivotMode=True,
        suppressAggFuncInHeader=True,
        grandTotalRow='bottom'
    )
    gb.configure_grid_options(
        autoGroupColumnDef=dict(
            minWidth=300,
            pinned='left',
            cellRendererParams=dict(suppressCount=True)
        )
    )

    go = gb.build()
    AgGrid(lead_df, gridOptions=go, height=400, fit_columns_on_grid_load=ColumnsAutoSizeMode.FIT_CONTENTS)
    # st.dataframe(lead_df)

def leads_cancellation(df, lead_reason):
    # Active Cancelled Lost pending
    new_df = df.copy()
    new_df['CancellationReason'] = np.where(new_df['CancellationReason'].isna(), 'Unknown', new_df['CancellationReason'])
    cancelled_df = df.loc[df['LeadStatus'] == lead_reason, ['CancellationReason', 'LeadStatus']].copy()

    gb = GridOptionsBuilder()

    gb.configure_default_column(
        resizable=True,
        filterable=True,
        sortable=True,
        editable=False
    )
    gb.configure_column(field='CancellationReason', header_name='Cancellation Reasons', width=80, rowGroup=True)

    gb.configure_column(
        field='LeadStatus',
        header_name='Total',
        aggFunc='count',
        valueFormatter='value.toLocaleString()',
        pivot=True,
        sort='desc'
    )
    gb.configure_grid_options(
        tooltipShowDelay=0,
        pivotMode=True,
        suppressAggFuncInHeader=True
    )
    gb.configure_grid_options(
        autoGroupColumnDef=dict(
            minWidth=300,
            pinned='left',
            cellRendererParams=dict(suppressCount=True)
        )
    )

    go = gb.build()
    AgGrid(cancelled_df, gridOptions=go, height=600, fit_columns_on_grid_load=ColumnsAutoSizeMode.FIT_CONTENTS)

def leads_cancellation_charts(df, lead_reason):
    new_df = df.copy()
    new_df['CancellationReason'] = np.where(new_df['CancellationReason'].isna(), 'Unknown', new_df['CancellationReason'])
    cancelled_df = new_df.loc[new_df['LeadStatus'] == lead_reason].copy()
    top_five = pd.DataFrame(cancelled_df.groupby('CancellationReason')['CancellationReason'].value_counts().sort_values(ascending=False)).reset_index()

    lead_pie = px.pie(top_five.head(5), values='count', names='CancellationReason', title=f"Top 5 reasons {lead_reason}")
    lead_pie.update_layout(title_x=0.42, legend_orientation='h', legend_indentation=20)

    container1 = st.container(border=True)
    return container1.plotly_chart(lead_pie, use_container_width=True, theme='streamlit')


df_selection = multi_select_filters(df)
metrics(df_selection)
st.markdown("")

nav_container = st.container(border=True)
with nav_container:
    report_radio = st.radio(
        label='Report Naviagion',
        options=['Lead Overview', 'Leads Per Source', 'Lost or Cancelled Leads'],
        horizontal=True,
    )
st.markdown('')

if report_radio == 'Lead Overview':
    st.markdown('<h3>Lead Overview</h3>', unsafe_allow_html=True)
    st.markdown('The below charts show an overview of the leads generated and their status. The first chart categorizes elements into 3 parts.')
    st.markdown(' - Lost Leads - All Leads with the status Cancelled, Lost or Unknown')
    st.markdown(' - Active Leads - All Leads with the status Active, Pending or New')
    st.markdown(' - Sold Leads - All Leads with the status Sold')
    lead_status_pie(df_selection)

elif report_radio == 'Leads Per Source':
    st.markdown('<h5>Lead Overview Per Lead Source</h5>', unsafe_allow_html=True)
    st.markdown('The below table shows all leads, grouped by the lead source and displays Active, Lost and Sold leads.')
    leads_per_source(df_selection)
    st.markdown('<h5>Lead Overview Per Brand and Lead Source</h5>', unsafe_allow_html=True)
    st.markdown('The below table shows all leads, grouped by the Brand and displays Active, Lost and Sold leads. This table is additionally grouped to show the lead source under the brand.')
    lead_per_source_per_brand(df_selection)

elif report_radio == 'Lost or Cancelled Leads':
    st.markdown('<h5>Lost Lead reasons Per Lead Status</h5>', unsafe_allow_html=True)
    lost_radio = st.radio(label='Lost Lead Radio', options=['All Lost or Cancellation Reasons', 'Top 5 reasons (Chart)'], label_visibility='hidden')

    if lost_radio == 'All Lost or Cancellation Reasons':
        st.markdown(' - The below is a comparison between leads marked as "Cancelled" and leads marked as "Lost", and shows the reasons from most common to least.')
        lc_col1, lc_col2 = st.columns(2)
        with lc_col1:
            st.markdown('<h6>Cancellation Reasons</h6>', unsafe_allow_html=True)
            leads_cancellation(df_selection, 'Cancelled')
        with lc_col2:
            st.markdown('<h6>Lost Reasons</h6>', unsafe_allow_html=True)
            leads_cancellation(df_selection, 'Lost')

    elif lost_radio == 'Top 5 reasons (Chart)':
        st.markdown(' - The below is a comparison of the top 5 reasons for both the Cancelled and Lost leads.')
        tf_col1, tf_col2 = st.columns(2)
        with tf_col1:
            top_five_df_c = leads_cancellation_charts(df_selection, 'Cancelled')
        with tf_col2:
            top_five_df_l = leads_cancellation_charts(df_selection, 'Lost')
    

# st.dataframe(df)
