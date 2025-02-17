
## SHIFT TRACKER

- A tool designed to streamline workforce management by enabling the tracking and monitoring of employee shifts, hours worked, and overall productivity. It integrates features such as scheduling, real-time attendance tracking, and reporting to provide businesses with a reliable means of ensuring efficient time management and adherence to labor compliance.

- Started the development on 20th of Dec 2024. 
- Work in progress.
- Proposed day for MVP presentation is on 23th od Jan 2025.

## SHIFT TRACKER WORK FLOW 

![Shift tracker flow chart drawio](https://github.com/user-attachments/assets/28a93b60-fb60-4b57-8e4f-c7831f119e22)

## LOGIN PAGE

![login](https://github.com/user-attachments/assets/b9128313-fc1a-4681-9632-0e469b129581)

## DASHBOARD

![Dashboard](https://github.com/user-attachments/assets/38e68d79-2c43-4879-9c1d-602e1cd6156b)

## ALLOCATED SHIFTS TO STAFF

![Shift page](https://github.com/user-attachments/assets/d3a0fb1d-9479-49c6-a543-23f91db1ea96)


## Project Structure

```## Project Structure.

Shift-Tracker/
│
├── README.md
├── manage.py
├── myenv/
├── static/
│
├── authentication/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   ├── views.py
│   └── migrations/
│
├── flow/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   ├── utils.py
│   ├── views.py
│   ├── context_processors.py
│   ├── templatetags/
│   └── migrations/
│
├── shift_tracker/
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
└── templates/
   ├── authentication/
   │   ├── edit_user.html
   │   ├── login.html
   │   ├── password_reset_request.html
   │   ├── register.html
   │   ├── set_new_password.html
   │   ├── user_list.html
   │   └── verify_otp.html
   │
   ├── flow/
   │   ├── admin_contact.html
   │   ├── assign_staff.html
   │   ├── base.html
   │   ├── create_schedule.html
   │   ├── edit_schedule.html
   │   ├── generate_schedule.html
   │   ├── home.html
   │   ├── intro.html
   │   ├── manage_holidays.html
   │   ├── staff_schedule.html
   │   ├── supervisor_dashboard.html
   │   ├── supervisor_schedule.html
   │   ├── team_staff_list.html
   │   ├── view_schedule.html
   │   ├── components/
   │   └── partial/
   │
   └── staff/
       ├── profile.html
       └── staff_list.html

## Setup and Installations 
    - Clone the repository (git clone [your-repository-url])
    - cd Shift-Tracker
    - python -m venv myenv
        source myenv/bin/activate  # On Linux/Mac
            # OR
        myenv\Scripts\activate  # On Windows
    - pip install -r requirements.txt
    - Connect and Verify you database connection 
    - python manage.py migrate  # On Windows
            # OR
        python3 manage.py migrate # On Linux/Mac
    - python manage.py runserver # On Windows
            # OR
      python3 manage.py runserver
     