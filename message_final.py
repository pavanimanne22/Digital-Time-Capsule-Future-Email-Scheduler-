
import streamlit as st
import mysql.connector
import re
import os
from datetime import datetime, date
from streamlit_autorefresh import st_autorefresh



import streamlit as st
st.set_page_config(page_title="Digital Time Capsule", page_icon="📨")
st.markdown("""
<style>
/* Make html and body fill the entire browser window */
html, body {
    height: 100%;
    margin: 0;
    padding: 0;
    overflow-x: hidden;
}

/* Animate background on the HTML layer */
body::before {
    content: "";
    position: fixed;
    top: 0; left: 0; bottom: 0; right: 0;
    z-index: -1;
    background: linear-gradient(-45deg, #ff9a9e, #fad0c4, #a18cd1, #fbc2eb);
    background-size: 400% 400%;
    animation: gradientBG 15s ease infinite;
}

/* Optional: make sidebar & main transparent to see animation */
.stApp {
    background: transparent;
}
[data-testid="stSidebar"] {
    background-color: rgba(255, 255, 255, 0.7);
}

/* Keyframes for gradient animation */
@keyframes gradientBG {
    0% {background-position: 0% 50%;}
    50% {background-position: 100% 50%;}
    100% {background-position: 0% 50%;}
}
</style>
""", unsafe_allow_html=True)





# Ensure upload directory exists
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Database connection
def connect_db():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database=""
    )
    cursor = conn.cursor()
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INT AUTO_INCREMENT PRIMARY KEY, 
                to_emails TEXT, 
                cc_emails TEXT, 
                bcc_emails TEXT,
                subject VARCHAR(255), 
                message_text TEXT, 
                scheduled_date DATETIME, 
                status ENUM('pending', 'sent') DEFAULT 'pending',
                attachment_path VARCHAR(500) NULL
            )
    """)
    conn.commit()
    return conn

# Load Messages from Database
def load_messages():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, to_emails, cc_emails, bcc_emails, subject, message_text, scheduled_date, status, attachment_path FROM messages")
    messages = cursor.fetchall()
    conn.close()
    return messages



import re
import dns.resolver

# Validate email formats and domain existence
def validate_emails(email_str):
    # Basic email pattern
    email_pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    emails = [e.strip() for e in email_str.split(',') if e.strip()]

    for email in emails:
        if not re.match(email_pattern, email):
            return f"Invalid format: {email}"

        domain = email.split('@')[-1]
        try:
            # Check domain has MX record (can receive emails)
            dns.resolver.resolve(domain, 'MX')
        except dns.resolver.NXDOMAIN:
            return f"Domain does not exist: {domain}"
        except dns.resolver.NoAnswer:
            return f"Domain has no MX record: {domain}"
        except Exception as e:
            return f"DNS check failed for {domain}: {e}"

    return True



# Streamlit UI
def main():
    st.markdown("""
<style>
/* Overall animated gradient background */
body, html, [data-testid="stAppViewContainer"] {
    background: linear-gradient(-45deg, #ff9a9e, #fad0c4, #a18cd1, #fbc2eb);
    background-size: 400% 600%;
    animation: gradientBG 15s ease infinite;
    background-repeat: no-repeat;
    background-position: center center;
    background-attachment: fixed;
    height: 100%;
    width: 100%;
    overflow-x: hidden;
}
@keyframes gradientBG {
    0% {background-position: 0% 50%;}
    50% {background-position: 100% 50%;}
    100% {background-position: 0% 50%;}
}

/* Main container */
.appview-container .main .block-container {
    background: linear-gradient(135deg, rgba(255,255,255,0.5), rgba(240,240,240,0.5));
    border-radius: 20px;
    padding: 3rem;
    margin-top: 50px;
    margin-bottom: 50px;
    max-width: 95%;
    min-height: 90vh;
    box-shadow: 0px 8px 30px rgba(0, 0, 0, 0.2);
    animation: blockGradient 12s ease-in-out infinite;
}
@keyframes blockGradient {
    0% {background: linear-gradient(135deg, #f6d365, #fda085);}
    50% {background: linear-gradient(135deg, #fda085, #f6d365);}
    100% {background: linear-gradient(135deg, #f6d365, #fda085);}
}

/* Beautiful "Get Started" button */
div.stButton > button:first-child {
    position: relative;
    overflow: hidden;
    background: linear-gradient(270deg, #ff416c, #ff4b2b, #ff416c);
    background-size: 600% 600%;
    animation: gradientMove 8s ease infinite, pulse 2s infinite;
    border: none;
    border-radius: 12px;
    padding: 0.8rem 1.5rem;
    font-size: 1.2rem;
    font-weight: bold;
    color: white;
    box-shadow: 0 0 10px rgba(255,75,43,0.5);
    transition: all 0.3s ease;
    z-index: 1;
}

@keyframes gradientMove {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}
@keyframes pulse {
    0% { box-shadow: 0 0 0 0 rgba(255, 75, 43, 0.6); }
    70% { box-shadow: 0 0 0 15px rgba(255, 75, 43, 0); }
    100% { box-shadow: 0 0 0 0 rgba(255, 75, 43, 0); }
}

/* Shine effect */
div.stButton > button:first-child::before {
    content: '';
    position: absolute;
    top: 0;
    left: -75%;
    width: 50%;
    height: 100%;
    background: linear-gradient(to right, rgba(255,255,255,0.3), rgba(255,255,255,0));
    transform: skewX(-20deg);
    animation: shine 2.5s infinite;
    z-index: 0;
}
@keyframes shine {
    0% { left: -75%; }
    100% { left: 125%; }
}

/* Hover boost */
div.stButton > button:first-child:hover {
    transform: scale(1.07);
    box-shadow: 0 0 25px rgba(255,75,43,0.9);
}
</style>
""", unsafe_allow_html=True)


    st.title("📨 Digital Time Capsule – Future Message Locker")

    # Initialize session state
    if "show_schedule" not in st.session_state:
        st.session_state.show_schedule = False

    if not st.session_state.show_schedule:
        st.subheader("👋 Welcome to Your Future Message Locker!")
        st.markdown("""
        Schedule messages to be delivered in the future! Whether it's a heartfelt note, a birthday wish, or a reminder – your message will be locked until the time comes.

        ### ✨ Features:
        - Email scheduling to specific future date & time
        - File attachments (PDF, Image, Video, etc.)
        - CC/BCC support
        - View or edit pending messages

        ---
        """)

        if st.button("🚀 Get Started"):
            st.session_state.show_schedule = True
            st.rerun()



    else:
        menu = ["Schedule Message", "View Messages","⬅️ Back to Get Started"]
        choice = st.sidebar.selectbox("Menu", menu)
        if choice == "Schedule Message":
            recipient = st.text_input("Recipient Email(s) (comma-separated)")
            cc = st.text_input("CC Email(s) (comma-separated, optional)")
            bcc = st.text_input("BCC Email(s) (comma-separated, optional)")
            MAX_SUBJECT_LENGTH = 60
            subject = st.text_input("Subject", max_chars=MAX_SUBJECT_LENGTH)
            MAX_MESSAGE_LENGTH = 5000
            message = st.text_area("Message", max_chars=MAX_MESSAGE_LENGTH)

            col1, col2 = st.columns(2)
            with col1:
                scheduled_date = st.date_input("Scheduled Date", min_value=date.today())
            with col2:
                scheduled_time = st.time_input("Scheduled Time")

            selected_datetime = datetime.combine(scheduled_date, scheduled_time)
            now = datetime.now()

            # Validate: only allow future datetime
            if scheduled_date == date.today() and selected_datetime < now:
                st.markdown("""
                        <div style="
                            background-color: #ff4d4f;
                            padding: 15px;
                            border-radius: 8px;
                            color: white;
                            font-weight: bold;
                            font-size: 16px;
                            margin-bottom: 10px;
                        ">
                        ⚠️ The selected time is in the past. Please choose a future time.
                        </div>
                        """, unsafe_allow_html=True)
            else:


                uploaded_file = st.file_uploader("Attach Files (Optional)", type=["jpg", "png", "pdf", "mp4", "docx"], accept_multiple_files=True)

                if st.button("Schedule Message"):
                    if not recipient.strip() or not subject.strip() or not message.strip():
                        st.error("All fields are required!")
                        return

                    if not validate_emails(recipient) or (cc and not validate_emails(cc)) or (bcc and not validate_emails(bcc)):
                        st.error("One or more email addresses are invalid!")
                        return

                    attachment_paths = []
                    if uploaded_file:
                        for file in uploaded_file:
                            file_path = os.path.join(UPLOAD_FOLDER, file.name)
                            with open(file_path, "wb") as f:
                                f.write(file.getbuffer())
                            attachment_paths.append(file_path)
                    attachment_path_str = ','.join(attachment_paths) if attachment_paths else None


                    scheduled_datetime = datetime.combine(scheduled_date, scheduled_time)
                    conn = connect_db()
                    cursor = conn.cursor()
                    cursor.execute(
                        """
                        INSERT INTO messages (to_emails, cc_emails, bcc_emails, subject, message_text, scheduled_date, status, attachment_path)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (recipient, cc, bcc, subject, message, scheduled_datetime, 'pending', attachment_path_str)
                    )
                    conn.commit()
                    conn.close()
                    st.success("Message scheduled successfully!")

        elif choice == "View Messages":
            # Automatically refresh every 10 seconds (10000 ms)
            st_autorefresh(interval=10000, key="view_message_refresh")
            messages = load_messages()

            if not messages:
                st.info("No messages scheduled.")
            else:
                for msg in messages:
                    msg_id, recipient, cc, bcc, subject, message_text, scheduled_date, status, attachment_path = msg
                    st.write(f"**To:** {recipient}")
                    if cc:
                        st.write(f"**CC:** {cc}")
                    if bcc:
                        st.write(f"**BCC:** {bcc}")
                    st.write(f"**Subject:** {subject}")
                    st.write(f"**Message:** {message_text}")
                    st.write(f"**Scheduled for:** {scheduled_date}")
                    st.write(f"**Status:** {status}")


                    if attachment_path:
                        attachments = attachment_path.split(',')
                        for path in attachments:
                            st.write(f"\U0001F4CE **Attachment:** {os.path.basename(path)}")



                    if status == 'pending':
                        now = datetime.now()
                        if scheduled_date > now:
                            if f"edit_mode_{msg_id}" not in st.session_state:
                                st.session_state[f"edit_mode_{msg_id}"] = False

                            col1, col2 = st.columns(2)

                            with col1:
                                if st.button(f"Cancel Message {msg_id}", key=f"cancel_{msg_id}"):
                                    conn = connect_db()
                                    cursor = conn.cursor()
                                    cursor.execute("DELETE FROM messages WHERE id = %s", (msg_id,))
                                    conn.commit()
                                    conn.close()
                                    st.success(f"Message {msg_id} has been canceled!")
                                    st.rerun()

                            with col2:
                                if not st.session_state[f"edit_mode_{msg_id}"]:
                                    if st.button(f"Edit Message {msg_id}", key=f"edit_{msg_id}"):
                                        st.session_state[f"edit_mode_{msg_id}"] = True
                                        st.rerun()
                                else:
                                    new_subject = st.text_input("New Subject", value=subject, key=f"new_subject_{msg_id}")
                                    new_message = st.text_area("New Message", value=message_text, key=f"new_message_{msg_id}")
                                    new_attachment = st.file_uploader(
                                                            "New Attachments (Optional)", 
                                                                type=["jpg", "png", "pdf", "mp4", "docx"], 
                                                                key=f"new_attachment_{msg_id}", 
                                                                accept_multiple_files=True
                                                            )
                                                                                                
                                    if st.button(f"Save Changes {msg_id}", key=f"save_changes_{msg_id}"):
                                        conn = connect_db()
                                        cursor = conn.cursor()

                                        if new_attachment:
                                            attachment_paths = []
                                            for file in new_attachment:
                                                file_path = os.path.join(UPLOAD_FOLDER, file.name)
                                                with open(file_path, "wb") as f:
                                                    f.write(file.getbuffer())
                                                attachment_paths.append(file_path)

                                            attachments_str = ",".join(attachment_paths)

                                            cursor.execute(
                                                "UPDATE messages SET subject = %s, message_text = %s, attachment_path = %s WHERE id = %s",
                                                (new_subject, new_message, attachments_str, msg_id)
                                            )
                                        else:
                                            # UPDATE without changing the attachment
                                            cursor.execute(
                                                "UPDATE messages SET subject = %s, message_text = %s WHERE id = %s",
                                                (new_subject, new_message, msg_id)
                                            )

                                        conn.commit()
                                        conn.close()

                                        st.success(f"Message {msg_id} has been updated!")
                                        st.session_state[f"edit_mode_{msg_id}"] = False
                                        st.rerun()

                        else:
                            st.info("⏳ This message is already scheduled or has been sent, so editing/canceling is disabled.")


                    st.write("---")
        elif choice == "⬅️ Back to Get Started":
            st.session_state.show_schedule = False
            st.rerun()
if __name__ == "__main__":
        main()
