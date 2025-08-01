app_name = "frappe_notifier"
app_title = "Frappe Notifier"
app_publisher = "Shahzad Bin Shahjahan"
app_description = "Push Notifications setup through Frappe Relay server"
app_email = "info@tridz.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "frappe_notifier",
# 		"logo": "/assets/frappe_notifier/logo.png",
# 		"title": "Frappe Notifier",
# 		"route": "/frappe_notifier",
# 		"has_permission": "frappe_notifier.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/frappe_notifier/css/frappe_notifier.css"
# app_include_js = "/assets/frappe_notifier/js/frappe_notifier.js"

# include js, css files in header of web template
# web_include_css = "/assets/frappe_notifier/css/frappe_notifier.css"
# web_include_js = "/assets/frappe_notifier/js/frappe_notifier.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "frappe_notifier/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "frappe_notifier/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "frappe_notifier.utils.jinja_methods",
# 	"filters": "frappe_notifier.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "frappe_notifier.install.before_install"
# after_install = "frappe_notifier.install.after_install"
after_install = "frappe_notifier.setup.setup_users"

# Uninstallation
# ------------

# before_uninstall = "frappe_notifier.uninstall.before_uninstall"
# after_uninstall = "frappe_notifier.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "frappe_notifier.utils.before_app_install"
# after_app_install = "frappe_notifier.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "frappe_notifier.utils.before_app_uninstall"
# after_app_uninstall = "frappe_notifier.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "frappe_notifier.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"frappe_notifier.tasks.all"
# 	],
# 	"daily": [
# 		"frappe_notifier.tasks.daily"
# 	],
# 	"hourly": [
# 		"frappe_notifier.tasks.hourly"
# 	],
# 	"weekly": [
# 		"frappe_notifier.tasks.weekly"
# 	],
# 	"monthly": [
# 		"frappe_notifier.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "frappe_notifier.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "frappe_notifier.event.get_events"
# }
override_whitelisted_methods = {
	'notification_relay.api.get_config': 'frappe_notifier.api.get_config.get_config',
    'notification_relay.api.token.add': 'frappe_notifier.api.token.add',
    'notification_relay.api.token.delete': 'frappe_notifier.api.token.remove',
    'notification_relay.api.send_notification.user': 'frappe_notifier.api.send_notification.user',
    'notification_relay.api.send_notification.topic': 'frappe_notifier.api.send_notification.topic',
    'notification_relay.api.topic.add':'frappe_notifier.api.topic.add',
    'notification_relay.api.topic.remove':'frappe_notifier.api.topic.remove',
    'notification_relay.api.topic.subscribe':'frappe_notifier.api.topic.subscribe',
    'notification_relay.api.topic.unsubscribe':'frappe_notifier.api.topic.unsubscribe'
}
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "frappe_notifier.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["frappe_notifier.utils.before_request"]
# after_request = ["frappe_notifier.utils.after_request"]

# Job Events
# ----------
# before_job = ["frappe_notifier.utils.before_job"]
# after_job = ["frappe_notifier.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"frappe_notifier.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

fixtures = [
    {
        "doctype":"Role",
        "filters":[
            [
                "name",
                "in",
                [
                    "FN Notification Manager"
                ]
            ]
        ]
    },
    {
        "doctype":"Custom DocPerm",
        "filters":[
            [
                "name",
                "in",
                [
                    "hc75io0kg9",
                    "b4hovd1ik7",
                    "s5gpbu441b",
                    "0u6la3me1b"
                ]
            ]
        ]
    }
]

