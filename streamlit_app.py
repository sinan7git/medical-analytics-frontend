# streamlit_app.py - Enhanced Medical Call Analytics Frontend
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
from collections import defaultdict

# Configuration
API_BASE_URL = "https://medical-call-analytics-api.onrender.com"

# Page config
st.set_page_config(
    page_title="Medical Call Analytics",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
def init_session_state():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_role' not in st.session_state:
        st.session_state.user_role = None
    if 'access_token' not in st.session_state:
        st.session_state.access_token = None
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'login_time' not in st.session_state:
        st.session_state.login_time = None
    if 'current_filters' not in st.session_state:
        st.session_state.current_filters = {}

# Token validation
def is_token_valid():
    if not st.session_state.access_token or not st.session_state.login_time:
        return False
    if datetime.now() - st.session_state.login_time > timedelta(hours=23):
        return False
    return True

def make_authenticated_request(endpoint, method="GET", data=None):
    headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
    url = f"{API_BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers)
        
        if response.status_code == 401:
            st.session_state.authenticated = False
            st.session_state.access_token = None
            st.session_state.user_role = None
            st.session_state.username = None
            st.session_state.login_time = None
            st.error("Session expired. Please log in again.")
            st.rerun()
            return None
        
        return response
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to the API server. Please make sure the FastAPI server is running.")
        return None

def login_page():
    st.title("🏥 Medical Call Analytics System")
    st.markdown("---")
    
    if is_token_valid() and st.session_state.access_token:
        response = make_authenticated_request("/health")
        if response and response.status_code == 200:
            st.session_state.authenticated = True
            st.rerun()
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.subheader("Login")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login", key="login_btn"):
            if not username or not password:
                st.error("Please enter both username and password")
                return
                
            try:
                response = requests.post(f"{API_BASE_URL}/api/auth/login", json={
                    "username": username,
                    "password": password
                })
                
                if response.status_code == 200:
                    data = response.json()
                    st.session_state.authenticated = True
                    st.session_state.access_token = data["access_token"]
                    st.session_state.user_role = data["role"]
                    st.session_state.username = username
                    st.session_state.login_time = datetime.now()
                    
                    st.success("Login successful!")
                    st.rerun()
                else:
                    error_detail = response.json().get("detail", "Invalid credentials")
                    st.error(f"Login failed: {error_detail}")
            except Exception as e:
                st.error(f"Login failed: {e}")
    
    with tab2:
        st.subheader("Register New User")
        reg_username = st.text_input("Username", key="reg_username")
        reg_email = st.text_input("Email", key="reg_email")
        reg_password = st.text_input("Password", type="password", key="reg_password")
        reg_role = st.selectbox("Role", ["manager"], key="reg_role")
        
        if st.button("Register", key="register_btn"):
            if not all([reg_username, reg_email, reg_password]):
                st.error("Please fill in all fields")
                return
                
            try:
                response = requests.post(f"{API_BASE_URL}/api/auth/register", json={
                    "username": reg_username,
                    "email": reg_email,
                    "password": reg_password,
                    "role": reg_role
                })
                
                if response.status_code == 200:
                    st.success("Registration successful! Please login.")
                else:
                    error_detail = response.json().get("detail", "Registration failed")
                    st.error(f"Registration failed: {error_detail}")
            except Exception as e:
                st.error(f"Registration failed: {e}")

def get_filter_options():
    """Get available filter options from API"""
    response = make_authenticated_request("/api/analytics/filter-options")
    if response and response.status_code == 200:
        return response.json()
    return {"locations": [], "services": [], "categories": [], "time_frames": []}


def dashboard_page():
    st.title("🏥 Medical Call Analytics")

    # Sidebar
    st.sidebar.markdown(f"**Welcome:** {st.session_state.username}")
    st.sidebar.markdown(f"**Role:** {st.session_state.user_role.title()}")

    if st.sidebar.button("Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    # Main tabs
    if st.session_state.user_role == "manager":
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Business Analytics",
            "🤖 AI Intelligence",
            "📋 Summary Reports",
            "📈 Executive Reports",
            "❓ Q&A"
        ])

        with tab1:
            enhanced_analytics_section()

        with tab2:
            enhanced_chat_section()

        with tab3:
            summary_reports_section()

        with tab4:
            executive_reports_section()

        with tab5:
            # Q&A Intelligence sub-tabs
            qa_subtab1, qa_subtab2, qa_subtab3 = st.tabs([
                "📊 Dashboard",
                "🔍 Manage Unique Questions",
                "📈 Analytics Charts",
            ])

            with qa_subtab1:
                qa_analytics_section()

            with qa_subtab2:
                unique_questions_management()

            with qa_subtab3:
                qa_insights_charts()



    else:
        # Receptionist/Staff view
        tab1, tab2 = st.tabs(["📞 Call Insights", "🤖 AI Assistant"])

        with tab1:
            basic_insights_section()

        with tab2:
            enhanced_chat_section()

def enhanced_analytics_section():
    """Enhanced analytics dashboard for managers"""
    st.subheader("📊 Business Intelligence Dashboard")
    
    # Get filter options
    filter_options = get_filter_options()
    
    # Filters Section
    st.markdown("### 🔍 Filters")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        date_from = st.date_input("From Date", datetime.now() - timedelta(days=30), key="date_from")
        
    with col2:
        date_to = st.date_input("To Date", datetime.now(), key="date_to")
    
    with col3:
        clinic_location = st.selectbox("Clinic Location", ["All"] + filter_options.get("locations", []), key="location_filter")
        
    with col4:
        service_type = st.selectbox("Service Type", ["All"] + filter_options.get("services", []), key="service_filter")
    
    col5, col6, col7 = st.columns(3)
    with col5:
        category = st.selectbox("Category", ["All"] + filter_options.get("categories", []), key="category_filter")
    with col6:
        time_frame = st.selectbox("Time Frame", filter_options.get("time_frames", ["week"]), key="time_frame")
    with col7:
        st.write("")  # Spacing
        apply_filters = st.button("Apply Filters 🔍", use_container_width=True)
    
    # Build filters object
    filters = {
        "date_from": str(date_from),
        "date_to": str(date_to),
        "clinic_location": clinic_location if clinic_location != "All" else None,
        "service_type": service_type if service_type != "All" else None,
        "category": category if category != "All" else None,
        "time_frame": time_frame
    }
    
    # Update session filters
    st.session_state.current_filters = filters
    
    st.markdown("---")
    
    # Main Dashboard Table
    st.markdown("### 📋 Time & Business Outcome Breakdown")
    
    try:
        response = make_authenticated_request("/api/analytics/time-breakdown", "POST", filters)
        if response and response.status_code == 200:
            data = response.json()
            breakdown = data["breakdown"]
            totals = data["totals"]
            total_calls = data["total_calls"]
            
            if total_calls > 0:
                # Create the breakdown table
                df_data = []
                for day, metrics in breakdown.items():
                    if metrics["Morning"] + metrics["Afternoon"] + metrics["Evening"] > 0:  # Only show days with calls
                        df_data.append({
                            "Day": day,
                            "Morning": metrics["Morning"],
                            "Afternoon": metrics["Afternoon"],
                            "Evening": metrics["Evening"],
                            "Didn't Book": metrics["Didn't Book"],
                            "Cancelled": metrics["Cancelled"],
                            "Other": metrics["Other"]
                        })
                
                # Add totals row
                df_data.append({
                    "Day": "**TOTALS**",
                    "Morning": totals["Morning"],
                    "Afternoon": totals["Afternoon"], 
                    "Evening": totals["Evening"],
                    "Didn't Book": totals["Didn't Book"],
                    "Cancelled": totals["Cancelled"],
                    "Other": totals["Other"]
                })
                
                df = pd.DataFrame(df_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                # Quick Stats Cards
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Calls", total_calls)
                with col2:
                    cancel_rate = round((totals["Cancelled"] / total_calls) * 100, 1) if total_calls > 0 else 0
                    st.metric("Cancellation Rate", f"{cancel_rate}%")
                with col3:
                    lost_rate = round((totals["Didn't Book"] / total_calls) * 100, 1) if total_calls > 0 else 0
                    st.metric("Lost Booking Rate", f"{lost_rate}%")
                with col4:
                    success_rate = round((totals["Other"] / total_calls) * 100, 1) if total_calls > 0 else 0
                    st.metric("Success Rate", f"{success_rate}%")
            else:
                st.info("No data available for the selected filters. Try adjusting your date range or filters.")
        else:
            st.error("Failed to load analytics data")
    except Exception as e:
        st.error(f"Error loading analytics: {e}")
    
    st.markdown("---")
    
    # Summary Statistics
    st.markdown("### 📈 Key Performance Insights")
    
    try:
        response = make_authenticated_request("/api/analytics/summary-stats", "POST", filters)
        if response and response.status_code == 200:
            stats = response.json()
            print(f"this is the summary : {stats}")
            
            if stats["total_calls"] > 0:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**📊 Peak Patterns:**")
                    st.write(f"• Peak Day: **{stats['peak_day']}**")
                    st.write(f"• Peak Time: **{stats['peak_time']}**")
                    st.write(f"• Top Location: **{stats['top_location']}**")
                    st.write(f"• Top Service: **{stats['top_service']}**")
                
                with col2:
                    st.markdown("**⚠️ Business Metrics:**")
                    st.write(f"• Cancellation Rate: **{stats['cancellation_rate']}%**")
                    st.write(f"• No Booking Rate: **{stats['no_booking_rate']}%**")
                    
                    if stats['cancellation_rate'] > 25:
                        st.warning("High cancellation rate detected!")
                    if stats['no_booking_rate'] > 30:
                        st.warning("High booking loss rate detected!")
                
                # Outcome Breakdown Chart
                if stats.get('outcome_breakdown'):
                    outcome_df = pd.DataFrame(list(stats['outcome_breakdown'].items()), 
                                            columns=['Outcome', 'Count'])
                    fig = px.pie(outcome_df, values='Count', names='Outcome', 
                               title="Business Outcomes Distribution")
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("Failed to load summary statistics")
    except Exception as e:
        st.error(f"Error loading summary stats: {e}")

def basic_insights_section():
    """Basic insights for receptionists"""
    st.subheader("📞 Call Insights & Patterns")
    
    # Simple metrics that are helpful for receptionists
    st.info("View general call patterns and get insights to help with customer service.")
    
    try:
        # Show basic location data
        response = make_authenticated_request("/api/analytics/calls-by-location")
        if response and response.status_code == 200:
            data = response.json()["data"]
            if data:
                df = pd.DataFrame(data)
                fig = px.bar(df, x="location", y="count", title="Calls by Location (This helps with workload planning)")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No call data available.")
    except Exception as e:
        st.error(f"Error loading data: {e}")

def enhanced_chat_section():
    """Enhanced chat section with filter integration"""
    st.subheader("🤖 AI Business Intelligence Assistant")
    
    # Show current filters if any
    if st.session_state.current_filters:
        with st.expander("📋 Current Filters Applied", expanded=False):
            filters = st.session_state.current_filters
            st.json(filters)
            st.info("The AI will analyze data based on these filters when you ask questions.")
    
    # Role-specific guidance
    if st.session_state.user_role == "manager":
        st.info("💼 Manager Mode: Ask about business performance, trends, and strategic insights.")
        example_queries = [
            "What's happening with our call performance?",
            "Why are we seeing so many cancellations?", 
            "What patterns do you see in Monday morning calls?",
            "How is Finsbury Park location performing?",
            "What's causing customers to book elsewhere?",
            "Give me insights about our children's services",
            "What time slots have availability issues?",
            "How can we improve our success rate?"
        ]
    else:
        st.info("📞 Receptionist Mode: Ask for customer service guidance and best practices.")
        example_queries = [
            "How should I handle urgent booking requests?",
            "What should I do when preferred slots are unavailable?",
            "Best way to handle cancellation requests?",
            "How to deal with upset customers?",
            "Which alternative locations should I suggest?",
            "What questions should I ask for children's services?",
            "How to handle refund requests?",
            "Tips for reducing no-shows?"
        ]
    
    # Example queries
    st.markdown("**💡 Try asking:**")
    cols = st.columns(2)
    for i, query in enumerate(example_queries[:6]):  # Show first 6
        with cols[i % 2]:
            if st.button(query, key=f"example_{i}", use_container_width=True):
                st.session_state.chat_input_value = query
                st.rerun()
    
    st.markdown("---")
    
    # Chat history display
    if st.session_state.chat_history:
        with st.container():
            st.markdown("### 💬 Conversation")
            for role, message in st.session_state.chat_history[-5:]:  # Show last 5 exchanges
                if role == "user":
                    st.markdown(f"**👤 You:** {message}")
                else:
                    st.markdown(f"**🤖 AI Assistant:** {message}")
                st.markdown("---")
    
    # Chat input
    if 'chat_input_value' not in st.session_state:
        st.session_state.chat_input_value = ""
    
    user_query = st.text_area(
        "Ask me anything about the medical calls:",
        value=st.session_state.chat_input_value,
        height=100,
        placeholder="e.g., What's causing our high Monday morning cancellation rate?"
    )
    
    col1, col2 = st.columns([1, 4])
    with col1:
        send_button = st.button("Send 📤", use_container_width=True)
        if st.button("Clear Chat", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.chat_input_value = ""
            st.rerun()
    
    if send_button and user_query.strip():
        # Add user message
        st.session_state.chat_history.append(("user", user_query))
        
        # Prepare chat request with filters
        chat_data = {
            "message": user_query,
            "filters": st.session_state.current_filters
        }
        
        try:
            with st.spinner("🤔 Analyzing your request..."):
                response = make_authenticated_request("/api/chat", "POST", chat_data)
                
                if response and response.status_code == 200:
                    ai_response = response.json()["response"]
                    st.session_state.chat_history.append(("assistant", ai_response))
                    st.session_state.chat_input_value = ""
                    st.rerun()
                else:
                    st.error("Failed to get AI response")
        except Exception as e:
            st.error(f"Error: {e}")

def executive_reports_section():
    """Executive reports for managers"""
    st.subheader("📈 Executive Reports & Analytics")
    
    st.markdown("### 📊 Generate Business Reports")
    
    col1, col2 = st.columns(2)
    with col1:
        report_date_from = st.date_input("Report From Date", datetime.now() - timedelta(days=30))
    with col2:
        report_date_to = st.date_input("Report To Date", datetime.now())
    
    report_type = st.selectbox(
        "Report Type",
        ["Executive Summary", "Location Performance", "Service Analysis", "Trend Analysis", "Competitive Analysis"]
    )
    
    if st.button("Generate Executive Report", use_container_width=True):
        filters = {
            "date_from": str(report_date_from),
            "date_to": str(report_date_to)
        }
        
        try:
            # Get comprehensive data
            breakdown_response = make_authenticated_request("/api/analytics/time-breakdown", "POST", filters)
            stats_response = make_authenticated_request("/api/analytics/summary-stats", "POST", filters)
            
            if breakdown_response and stats_response:
                breakdown_data = breakdown_response.json()
                stats_data = stats_response.json()
                
                st.success(f"✅ {report_type} Generated Successfully")
                
                # Executive Summary
                st.markdown(f"### 📋 {report_type}")
                st.markdown(f"**Report Period:** {report_date_from} to {report_date_to}")
                
                # Key Metrics
                st.markdown("#### 🎯 Key Performance Indicators")
                col1, col2, col3, col4 = st.columns(4)
                
                total_calls = breakdown_data["total_calls"]
                totals = breakdown_data["totals"]
                
                with col1:
                    st.metric("Total Calls", total_calls)
                with col2:
                    cancel_rate = round((totals["Cancelled"] / total_calls) * 100, 1) if total_calls > 0 else 0
                    st.metric("Cancellation Rate", f"{cancel_rate}%")
                with col3:
                    lost_rate = round((totals["Didn't Book"] / total_calls) * 100, 1) if total_calls > 0 else 0
                    st.metric("Lost Opportunity Rate", f"{lost_rate}%")
                with col4:
                    success_rate = round((totals["Other"] / total_calls) * 100, 1) if total_calls > 0 else 0
                    st.metric("Success Rate", f"{success_rate}%")
                
                # Business Insights
                st.markdown("#### 📈 Business Insights")
                insights = []
                
                if cancel_rate > 25:
                    insights.append(f"🚨 **High Cancellation Rate**: {cancel_rate}% is above recommended threshold of 25%")
                
                if lost_rate > 30:
                    insights.append(f"⚠️ **High Lost Booking Rate**: {lost_rate}% indicates availability or competitive issues")
                
                if stats_data.get("peak_day"):
                    insights.append(f"📊 **Peak Activity**: {stats_data['peak_day']} {stats_data['peak_time']} shows highest call volume")
                
                if totals["Morning"] > totals["Afternoon"] * 1.5:
                    insights.append("⏰ **Morning Peak**: Strong preference for morning appointments suggests capacity optimization opportunity")
                
                for insight in insights:
                    st.markdown(insight)
                
                # Recommendations
                st.markdown("#### 🎯 Strategic Recommendations")
                recommendations = []
                
                if cancel_rate > 25:
                    recommendations.append("1. Implement reminder call system to reduce cancellations")
                    recommendations.append("2. Review cancellation policy and introduce flexibility measures")
                
                if lost_rate > 20:
                    recommendations.append("3. Expand appointment availability during peak demand periods")
                    recommendations.append("4. Conduct competitive analysis for pricing and service offerings")
                
                if totals["Morning"] > totals["Afternoon"] * 1.3:
                    recommendations.append("5. Consider expanding morning capacity at high-demand locations")
                
                recommendations.append("6. Implement customer feedback system to identify improvement areas")
                
                for rec in recommendations:
                    st.markdown(rec)
                
                # Download capability
                report_data = {
                    "report_type": report_type,
                    "period": f"{report_date_from} to {report_date_to}",
                    "total_calls": total_calls,
                    "cancellation_rate": cancel_rate,
                    "lost_opportunity_rate": lost_rate,
                    "success_rate": success_rate,
                    "insights": insights,
                    "recommendations": recommendations
                }
                
                st.download_button(
                    "Download Report Data 📁",
                    data=json.dumps(report_data, indent=2),
                    file_name=f"{report_type.replace(' ', '_').lower()}_{report_date_from}_to_{report_date_to}.json",
                    mime="application/json"
                )
            else:
                st.error("Failed to generate report data")
        except Exception as e:
            st.error(f"Error generating report: {e}")


def summary_reports_section():
    st.subheader("📋 AI-Powered Summary Reports")

    daily_tab, monthly_tab, yearly_tab, overview_tab = st.tabs([
        "📅 Daily Summaries",
        "📊 Monthly Reports",
        "📈 Yearly Analysis",
        "🎯 Executive Overview"
    ])

    with daily_tab:
        daily_summaries_section()

    with monthly_tab:
        monthly_summaries_section()

    with yearly_tab:
        yearly_summaries_section()

    with overview_tab:
        executive_overview_section()


def daily_summaries_section():
    """Daily summaries management"""
    st.markdown("### 📅 Daily Performance Summaries")
    st.info("Generate and view AI-powered daily summaries of call performance, key metrics, and operational insights.")

    col1, col2 = st.columns([2, 1])

    with col1:
        # Date selection for new summary
        st.markdown("#### Generate New Daily Summary")
        target_date = st.date_input(
            "Select Date",
            value=datetime.now() - timedelta(days=1),  # Default to yesterday
            max_value=datetime.now().date(),
            key="daily_target_date"
        )

        if st.button("🚀 Generate Daily Summary", use_container_width=True):
            target_date_str = target_date.strftime("%Y-%m-%d")

            try:
                with st.spinner(f"🤖 Analyzing calls for {target_date_str}..."):
                    response = make_authenticated_request(
                        f"/api/summaries/generate-daily?target_date={target_date_str}",
                        "POST"
                    )

                    if response and response.status_code == 200:
                        result = response.json()
                        st.success(f"✅ Daily summary generated successfully!")

                        # Display the generated summary
                        display_daily_summary(result)
                    else:
                        error_msg = response.json().get("detail", "Unknown error") if response else "Connection failed"
                        st.error(f"❌ Failed to generate summary: {error_msg}")
            except Exception as e:
                st.error(f"Error generating daily summary: {e}")

    with col2:
        st.markdown("#### Quick Actions")

        # Generate summaries for last 7 days
        if st.button("📊 Generate Last 7 Days", use_container_width=True):
            generate_multiple_daily_summaries(7)

        # Generate summaries for last 30 days
        if st.button("📈 Generate Last 30 Days", use_container_width=True):
            generate_multiple_daily_summaries(30)

    st.markdown("---")

    # List existing daily summaries
    st.markdown("#### 📋 Recent Daily Summaries")

    try:
        response = make_authenticated_request("/api/summaries/daily?limit=14")  # Last 2 weeks
        if response and response.status_code == 200:
            summaries = response.json()

            if summaries:
                # Create a selection dropdown
                summary_options = [
                    f"{s['summary_date']} ({s['total_calls']} calls)"
                    for s in summaries
                ]

                selected_summary = st.selectbox(
                    "Select a daily summary to view:",
                    options=summary_options,
                    key="daily_summary_selector"
                )

                if selected_summary:
                    # Extract date from selection
                    selected_date = selected_summary.split(" (")[0]

                    # Get full summary details
                    detail_response = make_authenticated_request(f"/api/summaries/daily/{selected_date}")
                    if detail_response and detail_response.status_code == 200:
                        summary_detail = detail_response.json()
                        display_daily_summary_detail(summary_detail)
            else:
                st.info("No daily summaries found. Generate your first summary above!")
        else:
            st.error("Failed to load daily summaries")
    except Exception as e:
        st.error(f"Error loading daily summaries: {e}")


def monthly_summaries_section():
    """Monthly summaries management"""
    st.markdown("### 📊 Monthly Business Reports")
    st.info("Comprehensive monthly analysis with trends, insights, and strategic recommendations.")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("#### Generate Monthly Report")

        # Month/Year selection
        current_year = datetime.now().year
        year = st.selectbox("Year", range(current_year - 2, current_year + 1), index=2, key="monthly_year")
        month = st.selectbox("Month", range(1, 13),
                             format_func=lambda x: datetime(2000, x, 1).strftime("%B"),
                             index=datetime.now().month - 1, key="monthly_month")

        month_year = f"{year}-{month:02d}"

        if st.button("🚀 Generate Monthly Report", use_container_width=True):
            try:
                with st.spinner(f"🤖 Analyzing monthly data for {datetime(year, month, 1).strftime('%B %Y')}..."):
                    response = make_authenticated_request(
                        f"/api/summaries/generate-monthly?month_year={month_year}",
                        "POST"
                    )

                    if response and response.status_code == 200:
                        result = response.json()
                        st.success(f"✅ Monthly report generated successfully!")
                        display_monthly_summary(result)
                    else:
                        error_msg = response.json().get("detail", "Unknown error") if response else "Connection failed"
                        st.error(f"❌ Failed to generate report: {error_msg}")
            except Exception as e:
                st.error(f"Error generating monthly report: {e}")

    with col2:
        st.markdown("#### Report Info")
        st.markdown("""
        **Monthly reports include:**
        - 📊 Call volume trends
        - 🎯 Performance metrics
        - 📈 Week-over-week analysis
        - 💡 Strategic recommendations
        - 🔍 Service breakdown
        """)

    st.markdown("---")

    # List existing monthly summaries
    st.markdown("#### 📋 Monthly Reports Archive")

    try:
        response = make_authenticated_request("/api/summaries/monthly")
        if response and response.status_code == 200:
            summaries = response.json()

            if summaries:
                for summary in summaries[:6]:  # Show last 6 months
                    with st.expander(f"📊 {format_month_year(summary['month_year'])} - {summary['total_calls']} calls"):

                        # Get full details
                        detail_response = make_authenticated_request(f"/api/summaries/monthly/{summary['month_year']}")
                        if detail_response and detail_response.status_code == 200:
                            detail = detail_response.json()
                            display_monthly_summary_detail(detail)
            else:
                st.info("No monthly reports found. Generate your first report above!")
        else:
            st.error("Failed to load monthly summaries")
    except Exception as e:
        st.error(f"Error loading monthly summaries: {e}")


def yearly_summaries_section():
    """Yearly summaries management"""
    st.markdown("### 📈 Annual Strategic Analysis")
    st.info("High-level yearly performance analysis with strategic insights and long-term recommendations.")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("#### Generate Annual Report")

        current_year = datetime.now().year
        target_year = st.selectbox(
            "Select Year",
            range(current_year - 3, current_year + 1),
            index=3,  # Current year
            key="yearly_target"
        )

        if st.button("🚀 Generate Annual Report", use_container_width=True):
            try:
                with st.spinner(f"🤖 Analyzing annual data for {target_year}..."):
                    response = make_authenticated_request(
                        f"/api/summaries/generate-yearly?year={target_year}",
                        "POST"
                    )

                    if response and response.status_code == 200:
                        result = response.json()
                        st.success(f"✅ Annual report generated successfully!")
                        display_yearly_summary(result)

                        # Show data completeness info
                        if "data_completeness" in result:
                            completeness = result["data_completeness"]
                            if completeness["completion_rate"] < 100:
                                st.warning(
                                    f"📊 Data Completeness: {completeness['completion_rate']}% - Missing months: {', '.join(completeness['missing_months'])}")
                    else:
                        error_msg = response.json().get("detail", "Unknown error") if response else "Connection failed"
                        st.error(f"❌ Failed to generate report: {error_msg}")
            except Exception as e:
                st.error(f"Error generating annual report: {e}")

    with col2:
        st.markdown("#### Strategic Focus")
        st.markdown("""
        **Annual reports provide:**
        - 🎯 Year-over-year growth
        - 📊 Seasonal patterns
        - 🏆 Performance highlights
        - 🔮 Strategic recommendations
        - 💼 Board-ready insights
        """)

    st.markdown("---")

    # List existing yearly summaries
    st.markdown("#### 📋 Annual Reports Archive")

    try:
        response = make_authenticated_request("/api/summaries/yearly")
        if response and response.status_code == 200:
            summaries = response.json()

            if summaries:
                for summary in summaries:
                    with st.expander(f"📈 {summary['year']} Annual Report - {summary['total_calls']} calls"):

                        # Get full details
                        detail_response = make_authenticated_request(f"/api/summaries/yearly/{summary['year']}")
                        if detail_response and detail_response.status_code == 200:
                            detail = detail_response.json()
                            display_yearly_summary_detail(detail)
            else:
                st.info("No annual reports found. Generate your first report above!")
        else:
            st.error("Failed to load yearly summaries")
    except Exception as e:
        st.error(f"Error loading yearly summaries: {e}")


def executive_overview_section():
    """Executive dashboard overview"""
    st.markdown("### 🎯 Executive Dashboard")
    st.info("Consolidated view of daily, monthly, and yearly insights for strategic decision making.")

    try:
        response = make_authenticated_request("/api/summaries/executive-dashboard")
        if response and response.status_code == 200:
            dashboard = response.json()

            # Daily Snapshot
            st.markdown("#### 📅 Latest Daily Performance")
            daily = dashboard["daily_snapshot"]

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Recent Date", daily["date"] or "No data")
            with col2:
                st.metric("Daily Calls", daily["calls"])
            with col3:
                st.metric("Last Updated", format_datetime(daily["last_updated"]) if daily["last_updated"] else "Never")

            if daily["summary"]:
                st.markdown("**Daily Insights:**")
                st.write(daily["summary"])

            st.markdown("---")

            # Weekly Trends
            st.markdown("#### 📊 Weekly Trends")
            weekly = dashboard["weekly_trends"]

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Calls (7 days)", weekly["total_calls"])
            with col2:
                st.metric("Daily Average", f"{weekly['avg_calls_per_day']}")
            with col3:
                st.metric("Days Analyzed", weekly["days_analyzed"])

            st.markdown("---")

            # Monthly Insights
            st.markdown("#### 📈 Monthly Performance")
            monthly = dashboard["monthly_insights"]

            col1, col2 = st.columns([2, 1])
            with col1:
                if monthly["summary"]:
                    st.markdown("**Monthly Summary:**")
                    st.write(monthly["summary"])
            with col2:
                st.metric("Month", monthly["month"] or "No data")
                st.metric("Monthly Calls", monthly["calls"])

            if monthly["recommendations"]:
                st.markdown("**Key Recommendations:**")
                st.write(monthly["recommendations"])

            st.markdown("---")

            # Yearly Strategy
            st.markdown("#### 🎯 Strategic Overview")
            yearly = dashboard["yearly_strategy"]

            col1, col2 = st.columns([2, 1])
            with col1:
                if yearly["summary"]:
                    st.markdown("**Annual Performance:**")
                    st.write(yearly["summary"])
            with col2:
                st.metric("Year", yearly["year"] or "No data")
                st.metric("Annual Calls", yearly["calls"])

            if yearly["strategic_recommendations"]:
                st.markdown("**Strategic Recommendations:**")
                st.write(yearly["strategic_recommendations"])
        else:
            st.error("Failed to load executive dashboard")
    except Exception as e:
        st.error(f"Error loading executive dashboard: {e}")


def qa_analytics_section():
    """Q&A Analytics section for managers"""
    st.subheader("🤖 Q&A Intelligence Dashboard")

    # Get Q&A dashboard data
    try:
        dashboard_response = make_authenticated_request("/api/qa/dashboard")
        if dashboard_response and dashboard_response.status_code == 200:
            dashboard_data = dashboard_response.json()

            # Overview metrics
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "Total Q&A Pairs",
                    dashboard_data["database_a"]["total_qa_pairs"],
                    help="All question-answer pairs extracted from call transcripts"
                )

            with col2:
                st.metric(
                    "Unique Questions Found",
                    dashboard_data["database_b"]["total_unique_questions"],
                    help="Frequently asked questions (≥10 times)"
                )

            with col3:
                if dashboard_data["database_a"]["total_qa_pairs"] > 0:
                    uniqueness_rate = round(
                        (dashboard_data["database_b"]["total_unique_questions"] /
                         dashboard_data["database_a"]["total_qa_pairs"]) * 100, 1
                    )
                    st.metric("Uniqueness Rate", f"{uniqueness_rate}%", help="% of questions that are frequently asked")
                else:
                    st.metric("Uniqueness Rate", "0%")

            # Top unique questions
            if dashboard_data.get("top_unique_questions"):
                st.markdown("### 🎯 Most Frequently Asked Questions")

                for i, uq in enumerate(dashboard_data["top_unique_questions"], 1):
                    with st.expander(f"#{i}: Asked {uq['frequency']} times - {uq['business_impact'].title()} Priority"):
                        st.markdown(f"**❓ Question:** {uq['question']}")
                        st.markdown(f"**💬 Answer:** {uq['answer']}")
                        st.markdown(f"**📊 Priority Score:** {uq['priority_score']}")
                        st.markdown(f"**🎯 Business Impact:** {uq['business_impact'].title()}")
            else:
                st.info("No frequently asked questions found yet. Run unique question analysis to identify patterns.")

        else:
            st.error("Failed to load Q&A dashboard data")

    except Exception as e:
        st.error(f"Error loading Q&A data: {e}")


def unique_questions_management():
    """Manage and analyze unique questions"""
    # st.subheader("🔍 Unique Question Analysis")
    #
    # # Analysis controls
    col2 = st.columns(2)
    #
    # with col1:
    #     frequency_threshold = st.number_input(
    #         "Frequency Threshold",
    #         min_value=3,
    #         max_value=50,
    #         value=10,
    #         help="Questions asked this many times are considered 'unique'"
    #     )

    # with col2:
    #     st.write("")  # Spacing
    #     if st.button("🔄 Run Unique Analysis", type="primary"):
    #         with st.spinner("Analyzing question patterns..."):
    #             try:
    #                 analysis_response = make_authenticated_request(
    #                     "/api/qa/find-unique-questions",
    #                     "POST",
    #                     {"frequency_threshold": frequency_threshold}
    #                 )
    #
    #                 if analysis_response and analysis_response.status_code == 200:
    #                     result = analysis_response.json()
    #                     if result.get("status") == "success":
    #                         st.success(
    #                             f"✅ Found {result['unique_questions_found']} unique questions from {result['total_qa_pairs_analyzed']} Q&A pairs!")
    #                         st.rerun()
    #                     else:
    #                         st.error(f"Analysis failed: {result.get('error', 'Unknown error')}")
    #                 else:
    #                     st.error("Failed to run analysis")
    #
    #             except Exception as e:
    #                 st.error(f"Analysis error: {e}")
    #
    # st.markdown("---")

    # Filters for viewing unique questions
    st.markdown("### 📋 Browse Unique Questions")

    filter_col1, filter_col2, filter_col3 = st.columns(3)

    with filter_col1:
        category_filter = st.selectbox(
            "Category",
            ["All", "Availability", "Booking", "Pricing", "Service", "Location", "Cancellation", "Other"]
        )

    with filter_col2:
        impact_filter = st.selectbox(
            "Business Impact",
            ["All", "high", "medium", "low", "minimal"]
        )

    with filter_col3:
        min_freq_filter = st.number_input("Min Frequency", min_value=1, value=5)

    # Get filtered unique questions
    try:
        filters = {
            "min_frequency": min_freq_filter,
            "category": category_filter if category_filter != "All" else None,
            "business_impact": impact_filter if impact_filter != "All" else None
        }

        unique_response = make_authenticated_request("/api/qa/get-unique-questions", "POST", filters)

        if unique_response and unique_response.status_code == 200:
            unique_data = unique_response.json()
            unique_questions = unique_data.get("unique_questions", [])

            if unique_questions:
                st.write(f"Found {len(unique_questions)} unique questions:")

                # Display as expandable cards
                for uq in unique_questions:
                    # Color code by business impact
                    impact_colors = {
                        "high": "🔴",
                        "medium": "🟡",
                        "low": "🟢",
                        "minimal": "⚪"
                    }

                    impact_icon = impact_colors.get(uq["business_impact"], "⚪")

                    with st.expander(
                            f"{impact_icon} {uq['canonical_question']} (Asked {uq['frequency_count']} times)"
                    ):
                        col1, col2 = st.columns([2, 1])

                        with col1:
                            st.markdown(f"**📝 Answer:** {uq['canonical_answer']}")
                            st.markdown(f"**📂 Category:** {uq['category']}")

                            if uq.get('question_variations'):
                                show_variations = st.toggle("Show Question Variations", key=f"var_{uq['id']}")
                                if show_variations:
                                    for i, variation in enumerate(uq['question_variations'], 1):
                                        st.write(f"{i}. {variation}")

                        with col2:
                            st.metric("Frequency", uq['frequency_count'])
                            st.metric("Priority Score", f"{uq['priority_score']:.1f}")
                            st.write(f"**Impact:** {uq['business_impact'].title()}")
                            st.write(f"**Similarity:** {uq['avg_similarity_score']:.3f}")

                            if uq.get('locations_asked'):
                                st.write(f"**Locations:** {', '.join(uq['locations_asked'][:3])}")

                        # Recommended action
                        st.info(f"💡 **Action:** {uq['recommended_action']}")
            else:
                st.info("No unique questions found with current filters.")
        else:
            st.error("Failed to load unique questions")

    except Exception as e:
        st.error(f"Error loading unique questions: {e}")


def qa_insights_charts():
    """Q&A insights and visualizations"""
    st.subheader("📊 Q&A Analytics Charts")

    try:
        # Get unique questions for visualization
        unique_response = make_authenticated_request("/api/qa/get-unique-questions", "POST", {"min_frequency": 3})

        if unique_response and unique_response.status_code == 200:
            unique_data = unique_response.json()
            unique_questions = unique_data.get("unique_questions", [])

            if unique_questions:
                # Frequency distribution chart
                questions = [uq["canonical_question"][:50] + "..." if len(uq["canonical_question"]) > 50
                             else uq["canonical_question"] for uq in unique_questions]
                frequencies = [uq["frequency_count"] for uq in unique_questions]
                categories = [uq["category"] for uq in unique_questions]

                # Bar chart of top questions
                fig1 = go.Figure(data=[
                    go.Bar(
                        x=frequencies[:10],  # Top 10
                        y=questions[:10],
                        orientation='h',
                        text=frequencies[:10],
                        textposition='auto',
                        marker_color=['#FF6B6B' if freq >= 10 else '#4ECDC4' if freq >= 5 else '#45B7D1'
                                      for freq in frequencies[:10]]
                    )
                ])

                fig1.update_layout(
                    title="Top 10 Most Frequently Asked Questions",
                    xaxis_title="Frequency (Times Asked)",
                    yaxis_title="Questions",
                    height=600
                )

                st.plotly_chart(fig1, use_container_width=True)

                # Category breakdown pie chart
                category_counts = {}
                for uq in unique_questions:
                    cat = uq["category"]
                    category_counts[cat] = category_counts.get(cat, 0) + uq["frequency_count"]

                if category_counts:
                    fig2 = go.Figure(data=[
                        go.Pie(
                            labels=list(category_counts.keys()),
                            values=list(category_counts.values()),
                            hole=0.3
                        )
                    ])

                    fig2.update_layout(
                        title="Question Categories by Total Frequency",
                        height=400
                    )

                    st.plotly_chart(fig2, use_container_width=True)

                # Business impact distribution
                impact_counts = {}
                for uq in unique_questions:
                    impact = uq["business_impact"].title()
                    impact_counts[impact] = impact_counts.get(impact, 0) + 1

                if impact_counts:
                    col1, col2 = st.columns(2)

                    with col1:
                        fig3 = go.Figure(data=[
                            go.Bar(
                                x=list(impact_counts.keys()),
                                y=list(impact_counts.values()),
                                marker_color=['#FF6B6B', '#FFA500', '#4ECDC4', '#95A5A6']
                            )
                        ])

                        fig3.update_layout(
                            title="Questions by Business Impact",
                            height=300
                        )

                        st.plotly_chart(fig3, use_container_width=True)

                    with col2:
                        # Priority score distribution
                        priority_scores = [uq["priority_score"] for uq in unique_questions]

                        fig4 = go.Figure(data=[
                            go.Histogram(
                                x=priority_scores,
                                nbinsx=10,
                                marker_color='#45B7D1'
                            )
                        ])

                        fig4.update_layout(
                            title="Priority Score Distribution",
                            xaxis_title="Priority Score",
                            yaxis_title="Number of Questions",
                            height=300
                        )

                        st.plotly_chart(fig4, use_container_width=True)
            else:
                st.info("No unique questions available for visualization. Run the analysis first.")
        else:
            st.error("Failed to load data for charts")

    except Exception as e:
        st.error(f"Error creating charts: {e}")

# Helper functions for displaying summaries

def display_daily_summary(result):
    """Display generated daily summary results"""
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Date", result["date"])
    with col2:
        st.metric("Total Calls", result["total_calls"])
    with col3:
        st.metric("Status", "✅ Generated")

    st.markdown("**AI Summary:**")
    st.write(result["summary"])

    # Key metrics
    if "metrics" in result:
        metrics = result["metrics"]
        st.markdown("**Key Metrics:**")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Top Service", metrics.get("top_service", "N/A"))
        with col2:
            st.metric("Busiest Location", metrics.get("busiest_location", "N/A"))
        with col3:
            st.metric("Cancellation Rate", f"{metrics.get('cancelled_rate', 0)}%")
        with col4:
            st.metric("No Booking Rate", f"{metrics.get('no_booking_rate', 0)}%")


def display_daily_summary_detail(summary):
    """Display detailed daily summary"""
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Calls", summary["total_calls"])
    with col2:
        st.metric("Generated", format_datetime(summary["generated_at"]))
    with col3:
        if summary["key_metrics"].get("cancelled_rate", 0) > 25:
            st.error("⚠️ High Cancellation Rate")
        else:
            st.success("✅ Performance OK")

    st.markdown("**Summary:**")
    st.write(summary["summary_text"])

    # Expandable metrics
    with st.expander("📊 Detailed Metrics"):
        st.json(summary["key_metrics"])


def display_monthly_summary(result):
    """Display generated monthly summary results"""
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Month", format_month_year(result["month_year"]))
    with col2:
        st.metric("Total Calls", result["total_calls"])
    with col3:
        st.metric("Status", "✅ Generated")

    st.markdown("**Executive Summary:**")
    st.write(result["summary"])

    st.markdown("**Strategic Recommendations:**")
    st.write(result["recommendations"])


def display_monthly_summary_detail(summary):
    """Display detailed monthly summary"""
    st.markdown("**Executive Summary:**")
    st.write(summary["summary_text"])

    st.markdown("**Strategic Recommendations:**")
    st.write(summary["recommendations"])

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Calls", summary["total_calls"])
    with col2:
        st.metric("Generated", format_datetime(summary["generated_at"]))

    with st.expander("📊 Key Insights"):
        st.json(summary["key_insights"])


def display_yearly_summary(result):
    """Display generated yearly summary results"""
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Year", result["year"])
    with col2:
        st.metric("Total Calls", result["total_calls"])
    with col3:
        st.metric("Status", "✅ Generated")

    st.markdown("**Annual Summary:**")
    st.write(result["summary"])

    st.markdown("**Strategic Recommendations:**")
    st.write(result["recommendations"])


def display_yearly_summary_detail(summary):
    """Display detailed yearly summary"""
    st.markdown("**Annual Performance Summary:**")
    st.write(summary["summary_text"])

    st.markdown("**Strategic Recommendations:**")
    st.write(summary["strategic_recommendations"])

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Calls", summary["total_calls"])
    with col2:
        st.metric("Generated", format_datetime(summary["generated_at"]))

    with st.expander("📊 Key Insights"):
        st.json(summary["key_insights"])


def generate_multiple_daily_summaries(days):
    """Generate daily summaries for multiple days"""
    success_count = 0
    error_count = 0

    progress_bar = st.progress(0)
    status_text = st.empty()

    for i in range(days):
        target_date = datetime.now() - timedelta(days=days - i)
        target_date_str = target_date.strftime("%Y-%m-%d")

        status_text.text(f"Generating summary for {target_date_str}...")

        try:
            response = make_authenticated_request(
                f"/api/summaries/generate-daily?target_date={target_date_str}",
                "POST"
            )

            if response and response.status_code == 200:
                success_count += 1
            else:
                error_count += 1
        except:
            error_count += 1

        progress_bar.progress((i + 1) / days)

    status_text.text(f"Completed! ✅ {success_count} generated, ❌ {error_count} failed")


# Utility functions

def format_month_year(month_year_str):
    """Format YYYY-MM to 'Month YYYY'"""
    try:
        year, month = month_year_str.split('-')
        return datetime(int(year), int(month), 1).strftime("%B %Y")
    except:
        return month_year_str


def format_datetime(dt_str):
    """Format datetime string for display"""
    if not dt_str:
        return "Unknown"
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return str(dt_str)[:16]  # Fallback


def check_server_connection():
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def main():
    init_session_state()
    
    if not check_server_connection():
        st.error("🚫 Cannot connect to the API server. Please make sure the FastAPI server is running on https://medical-call-analytics-api.onrender.com")
        st.info("To start the server, run: `python main.py`")
        return
    
    if not st.session_state.authenticated and is_token_valid() and st.session_state.access_token:
        response = make_authenticated_request("/health")
        if response and response.status_code == 200:
            st.session_state.authenticated = True
    
    if not st.session_state.authenticated:
        login_page()
    else:
        dashboard_page()

if __name__ == "__main__":
    main()