from django.core.management.base import BaseCommand
from flow.models import FAQCategory, FAQ
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Populate the database with sample FAQ data'

    def handle(self, *args, **options):
        # Create FAQ Categories
        categories_data = [
            {
                'name': 'Getting Started',
                'description': 'Basic questions about using Shift Tracker',
                'order': 1
            },
            {
                'name': 'Scheduling',
                'description': 'Questions about creating and managing schedules',
                'order': 2
            },
            {
                'name': 'Time Tracking',
                'description': 'Questions about tracking work hours and attendance',
                'order': 3
            },
            {
                'name': 'Reports & Analytics',
                'description': 'Questions about generating reports and viewing analytics',
                'order': 4
            },
            {
                'name': 'Account Management',
                'description': 'Questions about user accounts and permissions',
                'order': 5
            },
            {
                'name': 'Troubleshooting',
                'description': 'Common issues and their solutions',
                'order': 6
            }
        ]

        # Create categories
        created_categories = {}
        for cat_data in categories_data:
            category, created = FAQCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'description': cat_data['description'],
                    'order': cat_data['order']
                }
            )
            created_categories[cat_data['name']] = category
            if created:
                self.stdout.write(f"Created category: {category.name}")

        # Sample FAQ data
        faqs_data = [
            # Getting Started
            {
                'category': 'Getting Started',
                'question': 'How do I log into Shift Tracker?',
                'answer': 'To log into Shift Tracker, navigate to the login page and enter your username and password. If you forgot your password, click on "Forgot Password" to reset it. If you don\'t have an account yet, contact your administrator to create one for you.',
                'order': 1
            },
            {
                'category': 'Getting Started',
                'question': 'What is Shift Tracker and how does it work?',
                'answer': 'Shift Tracker is a workforce management tool that helps businesses track employee shifts, monitor work hours, and manage schedules. It allows supervisors to create schedules, employees to view their shifts, track attendance, and generate reports for better workforce management.',
                'order': 2
            },
            {
                'category': 'Getting Started',
                'question': 'How do I navigate the dashboard?',
                'answer': 'The dashboard is your main control center. Use the sidebar menu to navigate between different sections like Home, Schedules, Staff Management, and Reports. The top navigation bar shows your profile and notification options. Each section has its own set of tools and features.',
                'order': 3
            },

            # Scheduling
            {
                'category': 'Scheduling',
                'question': 'How do I create a new schedule?',
                'answer': 'To create a new schedule, go to the Scheduling section and click "Create Schedule". Fill in the required information including shift times, assigned staff, and dates. You can create recurring schedules or one-time shifts. Don\'t forget to save your changes.',
                'order': 1
            },
            {
                'category': 'Scheduling',
                'question': 'Can I assign multiple staff members to one shift?',
                'answer': 'Yes, you can assign multiple staff members to a single shift. When creating or editing a schedule, use the staff assignment feature to select multiple employees. This is useful for shifts that require multiple people working together.',
                'order': 2
            },
            {
                'category': 'Scheduling',
                'question': 'How do I handle schedule conflicts?',
                'answer': 'The system will automatically detect scheduling conflicts when an employee is assigned to overlapping shifts. When conflicts are detected, you\'ll see a warning message. You can resolve conflicts by adjusting shift times, reassigning staff, or splitting shifts.',
                'order': 3
            },
            {
                'category': 'Scheduling',
                'question': 'Can employees request time off through the system?',
                'answer': 'Time off requests depend on your system configuration. If enabled, employees can submit time off requests through their profile. These requests will appear in your scheduling dashboard for approval. Check with your administrator about this feature availability.',
                'order': 4
            },

            # Time Tracking
            {
                'category': 'Time Tracking',
                'question': 'How do employees clock in and out?',
                'answer': 'Employees can clock in and out through their dashboard. The system records the exact time and can use GPS location if enabled. Supervisors can also manually adjust clock-in/out times if needed for corrections.',
                'order': 1
            },
            {
                'category': 'Time Tracking',
                'question': 'What happens if an employee forgets to clock out?',
                'answer': 'If an employee forgets to clock out, supervisors can manually add the clock-out time through the time tracking section. The system may also send reminders to employees about incomplete time entries.',
                'order': 2
            },
            {
                'category': 'Time Tracking',
                'question': 'How are overtime hours calculated?',
                'answer': 'Overtime is automatically calculated based on your company\'s policies. Typically, any hours worked over 8 hours per day or 40 hours per week are considered overtime. The system will highlight overtime hours in reports and calculate them at the appropriate rate.',
                'order': 3
            },

            # Reports & Analytics
            {
                'category': 'Reports & Analytics',
                'question': 'What types of reports can I generate?',
                'answer': 'You can generate various reports including attendance reports, hours worked summaries, overtime reports, schedule compliance reports, and productivity analytics. Reports can be filtered by date range, employee, department, or other criteria.',
                'order': 1
            },
            {
                'category': 'Reports & Analytics',
                'question': 'How do I export reports?',
                'answer': 'Most reports can be exported in multiple formats including PDF, Excel, and CSV. Look for the export button in the reports section. You can also schedule automatic report generation and email delivery.',
                'order': 2
            },
            {
                'category': 'Reports & Analytics',
                'question': 'Can I customize report templates?',
                'answer': 'Yes, many report templates can be customized. You can choose which columns to include, set date ranges, apply filters, and save custom report templates for future use. This helps you create reports that match your specific business needs.',
                'order': 3
            },

            # Account Management
            {
                'category': 'Account Management',
                'question': 'How do I add new employees to the system?',
                'answer': 'To add new employees, go to the Staff Management section and click "Add New Employee". Fill in the required information including name, contact details, role, and permissions. New employees will receive login credentials via email.',
                'order': 1
            },
            {
                'category': 'Account Management',
                'question': 'What are the different user roles available?',
                'answer': 'The system typically includes roles like Administrator (full access), Supervisor (manage schedules and staff), and Employee (view own schedule and clock in/out). Each role has specific permissions and access levels.',
                'order': 2
            },
            {
                'category': 'Account Management',
                'question': 'How do I reset an employee\'s password?',
                'answer': 'Administrators can reset employee passwords through the User Management section. Select the employee and click "Reset Password". The employee will receive an email with instructions to set a new password.',
                'order': 3
            },

            # Troubleshooting
            {
                'category': 'Troubleshooting',
                'question': 'The system is running slowly. What should I do?',
                'answer': 'Slow performance can be caused by various factors. Try refreshing your browser, clearing cache and cookies, or using a different browser. If the problem persists, check your internet connection or contact technical support.',
                'order': 1
            },
            {
                'category': 'Troubleshooting',
                'question': 'I can\'t see my schedule. What\'s wrong?',
                'answer': 'If you can\'t see your schedule, check if you\'re looking at the correct date range. Ensure you have proper permissions to view schedules. If the problem continues, contact your supervisor or system administrator.',
                'order': 2
            },
            {
                'category': 'Troubleshooting',
                'question': 'How do I report a bug or technical issue?',
                'answer': 'To report bugs or technical issues, use the Contact Support feature in the system. Provide detailed information about the problem, including what you were doing when it occurred, error messages, and your browser information.',
                'order': 3
            },
        ]

        # Get or create a default admin user for FAQ creation
        admin_user, created = User.objects.get_or_create(
            email='admin@example.com',
            defaults={
                'first_name': 'Admin',
                'last_name': 'User',
                'is_staff': True, 
                'is_superuser': True
            }
        )

        # Create FAQs
        created_count = 0
        for faq_data in faqs_data:
            category = created_categories[faq_data['category']]
            
            faq, created = FAQ.objects.get_or_create(
                question=faq_data['question'],
                category=category,
                defaults={
                    'answer': faq_data['answer'],
                    'order': faq_data['order'],
                    'created_by': admin_user
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(f"Created FAQ: {faq.question[:50]}...")

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {len(created_categories)} categories and {created_count} FAQs'
            )
        )