from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SelectField, TextAreaField, FileField, DecimalField, IntegerField, HiddenField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, NumberRange, ValidationError
from flask_wtf.file import FileAllowed, FileRequired
import re
from flask_wtf import FlaskForm
from wtforms import (
    StringField, TextAreaField, SelectField, DecimalField,
    BooleanField, SubmitField        # ← add this
)
from wtforms.validators import DataRequired, Optional, NumberRange

def validate_password_strength(form, field):
    """Validate password strength"""
    password = field.data
    if len(password) < 8:
        raise ValidationError('Password must be at least 8 characters long')
    if not re.search(r'[A-Z]', password):
        raise ValidationError('Password must contain at least one uppercase letter')
    if not re.search(r'[a-z]', password):
        raise ValidationError('Password must contain at least one lowercase letter')
    if not re.search(r'[0-9]', password):
        raise ValidationError('Password must contain at least one number')

class LoginForm(FlaskForm):
    """Login form"""
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')

class RegistrationForm(FlaskForm):
    """Registration form"""
    email_or_phone = StringField(
    'Email or Phone',
    validators=[DataRequired(), Length(min=5, max=120)],
    render_kw={"placeholder": "e.g. juan@mail.com or +639171234567"}
    )
    phone = HiddenField()   # we’ll store the cleaned phone here
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=50)])
    password = PasswordField('Password', validators=[DataRequired(), validate_password_strength])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(), EqualTo('password', message='Passwords must match')
    ])
    role = SelectField('Account Type', choices=[
        ('job_seeker', 'Job Seeker'),
        ('business_owner', 'Business Owner')
        # ('service_client', 'Service Client')
    ], validators=[DataRequired()])

class PasswordResetForm(FlaskForm):
    """Password reset request form"""
    email = StringField('Email', validators=[DataRequired(), Email()])

class PasswordChangeForm(FlaskForm):
    """Password change form"""
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), validate_password_strength])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(), EqualTo('new_password', message='New passwords must match')
    ])

class BusinessForm(FlaskForm):
    """Business registration form"""
    name = StringField('Business Name', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(min=10, max=1000)])
    category = SelectField('Category', choices=[
        ('restaurant', 'Restaurant'),
        ('retail', 'Retail'),
        ('services', 'Services'),
        ('manufacturing', 'Manufacturing'),
        ('healthcare', 'Healthcare'),
        ('education', 'Education'),
        ('technology', 'Technology'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    address = StringField('Address', validators=[DataRequired(), Length(min=5, max=200)])
    phone = StringField('Phone', validators=[DataRequired(), Length(min=10, max=20)])
    email = StringField('Business Email', validators=[DataRequired(), Email()])
    website = StringField('Website', validators=[Optional(), Length(max=100)])
    permit_number = StringField('Business Permit Number', validators=[DataRequired(), Length(min=5, max=50)])
    permit_file = FileField('Business Permit', validators=[
        FileRequired(),
        FileAllowed(['pdf', 'jpg', 'jpeg', 'png'], 'Only PDF and image files are allowed')
    ])

class JobForm(FlaskForm):
    """Job posting form"""
    business_id = SelectField('Business', validators=[DataRequired()], coerce=str)
    title = StringField('Job Title', validators=[DataRequired(), Length(min=3, max=100)])
    description = TextAreaField('Job Description', validators=[DataRequired(), Length(min=20, max=2000)])
    category = SelectField('Category', choices=[
        ('technology', 'Technology'),
        ('healthcare', 'Healthcare'),
        ('education', 'Education'),
        ('retail', 'Retail'),
        ('hospitality', 'Hospitality'),
        ('construction', 'Construction'),
        ('manufacturing', 'Manufacturing'),
        ('services', 'Services'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    type = SelectField('Job Type', choices=[
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
        ('internship', 'Internship')
    ], validators=[DataRequired()])
    salary_min = DecimalField('Minimum Salary', validators=[Optional(), NumberRange(min=0)])
    salary_max = DecimalField('Maximum Salary', validators=[Optional(), NumberRange(min=0)])
    currency = SelectField('Currency', choices=[
        ('PHP', 'Philippine Peso (PHP)'),
        ('USD', 'US Dollar (USD)'),
        ('EUR', 'Euro (EUR)')
    ], default='PHP', validators=[DataRequired()])
    location = StringField('Job Location', validators=[DataRequired(), Length(min=3, max=100)])
    requirements = TextAreaField('Requirements', validators=[Optional(), Length(max=1000)])
    benefits = TextAreaField('Benefits', validators=[Optional(), Length(max=1000)])
    requirements_file = FileField('Requirements Document', validators=[
        Optional(),
        FileAllowed(['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'], 'Only PDF, DOC, DOCX, and image files are allowed')
    ])
    expires_at = StringField('Application Deadline', validators=[Optional()])

# class ServiceForm(FlaskForm):
#     """Service posting form"""
#     title = StringField('Service Title', validators=[DataRequired(), Length(min=3, max=100)])
#     description = TextAreaField('Service Description', validators=[DataRequired(), Length(min=20, max=1000)])
#     category = SelectField('Category', choices=[
#         ('home_services', 'Home Services'),
#         ('professional_services', 'Professional Services'),
#         ('personal_services', 'Personal Services'),
#         ('automotive', 'Automotive'),
#         ('health_wellness', 'Health & Wellness'),
#         ('education_training', 'Education & Training'),
#         ('creative_media', 'Creative & Media'),
#         ('other', 'Other')
#     ], validators=[DataRequired()])
#     price = DecimalField('Price', validators=[DataRequired(), NumberRange(min=0)])
#     price_type = SelectField('Price Type', choices=[
#         ('fixed', 'Fixed Price'),
#         ('hourly', 'Per Hour'),
#         ('daily', 'Per Day')
#     ], validators=[DataRequired()])
#     location = StringField('Service Location', validators=[DataRequired(), Length(min=3, max=100)])
#     duration = StringField('Estimated Duration', validators=[Optional(), Length(max=50)])
#     requirements = TextAreaField('Requirements', validators=[Optional(), Length(max=500)])

class ReviewForm(FlaskForm):
    """Review form"""
    rating = IntegerField('Rating', validators=[DataRequired(), NumberRange(min=1, max=5)])
    comment = TextAreaField('Comment', validators=[Optional(), Length(max=500)])

class ProfileForm(FlaskForm):
    """User profile form"""
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=50)])
    phone = StringField('Phone', validators=[Optional(), Length(min=10, max=20)])
    location = StringField('Location', validators=[Optional(), Length(max=100)])
    profile_picture = FileField('Profile Picture', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png'], 'Only image files are allowed')
    ])

class SearchForm(FlaskForm):
    """Search form"""
    query = StringField('Search', validators=[Optional(), Length(max=100)])
    category = SelectField('Category', choices=[('', 'All Categories')], validators=[Optional()])
    location = StringField('Location', validators=[Optional(), Length(max=100)])
    sort_by = SelectField('Sort By', choices=[
        ('created_at', 'Newest'),
        ('rating', 'Highest Rated'),
        ('name', 'Name A-Z')
    ], validators=[Optional()])

class JobApplicationForm(FlaskForm):
    """Job application form"""
    cover_letter = TextAreaField('Cover Letter', validators=[DataRequired(), Length(min=50, max=2000)])
    resume = FileField('Resume', validators=[
        FileRequired(),
        FileAllowed(['pdf', 'doc', 'docx'], 'Only PDF and Word documents are allowed')
    ])

class ContactForm(FlaskForm):
    """Contact form"""
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    subject = StringField('Subject', validators=[DataRequired(), Length(min=5, max=200)])
    message = TextAreaField('Message', validators=[DataRequired(), Length(min=10, max=2000)])
from wtforms import StringField, DecimalField, SelectField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, Optional, NumberRange

# class ServiceForm(FlaskForm):
#     """Form for creating / editing a service listing"""

#     title = StringField('Service Title', validators=[DataRequired()])
#     description = TextAreaField('Description', validators=[DataRequired()])
    
#     category = SelectField(
#         'Category',
#         choices=[
#             ('tech', 'Technology & IT'),
#             ('design', 'Design & Creative'),
#             ('writing', 'Writing & Translation'),
#             ('marketing', 'Marketing & Sales'),
#             ('business', 'Business & Consulting'),
#             ('legal', 'Legal'),
#             ('accounting', 'Accounting & Finance'),
#             ('engineering', 'Engineering & Architecture'),
#             ('education', 'Teaching & Education'),
#             ('health', 'Health & Wellness'),
#             ('events', 'Events & Entertainment'),
#             ('other', 'Other')
#         ],
#         validators=[DataRequired()]
#     )

#     price = DecimalField('Price (numbers only)', validators=[NumberRange(min=0)])
    
#     currency = SelectField(
#         'Currency',
#         choices=[('PHP', '₱ PHP'), ('USD', '$ USD')],
#         default='PHP'
#     )

#     price_type = SelectField(
#         'Pricing model',
#         choices=[
#             ('fixed', 'Fixed price'),
#             ('hourly', 'Per hour'),
#             ('daily', 'Per day'),
#             ('project', 'Per project')
#         ],
#         default='fixed'
#     )

#     location = StringField('Location / City', validators=[DataRequired()])
#     duration = StringField('Estimated duration (optional)', validators=[Optional()])
#     requirements = TextAreaField('Client requirements (optional)', validators=[Optional()])
#     is_active = BooleanField('List as active', default=True)
    
#     submit = SubmitField('Save Service')


class VerificationForm(FlaskForm):
    """Form for identity verification document upload"""
    id_document = FileField('ID Document', validators=[
        FileRequired(),
        FileAllowed(['pdf', 'png', 'jpg', 'jpeg'], 'PDF, PNG, JPG only')
    ])
    id_number = StringField('ID Number', validators=[
        DataRequired(),
        Length(min=5, max=50)
    ])
    id_expiry = StringField('ID Expiry Date', validators=[Optional()])
    
    business_permit = FileField('Business Permit', validators=[
        FileAllowed(['pdf', 'png', 'jpg', 'jpeg'], 'PDF, PNG, JPG only')
    ])
    
    dti_registration = FileField('DTI Registration', validators=[
        FileAllowed(['pdf', 'png', 'jpg', 'jpeg'], 'PDF, PNG, JPG only')
    ])
    
    business_address = TextAreaField('Business Address', validators=[Optional()])
    
    resume = FileField('Resume/CV', validators=[
        FileAllowed(['pdf', 'doc', 'docx'], 'PDF or Word document only')
    ])
    
    certifications = FileField('Certifications', validators=[
        FileAllowed(['pdf', 'png', 'jpg', 'jpeg'], 'PDF, PNG, JPG only')
    ], render_kw={'multiple': True})
    
    address_proof = FileField('Address Proof', validators=[
        FileAllowed(['pdf', 'png', 'jpg', 'jpeg'], 'PDF, PNG, JPG only')
    ])
    
    terms = BooleanField('I agree to the terms and conditions', validators=[DataRequired()])
    
    submit = SubmitField('Submit for Verification')