from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import SelectField, TextAreaField
from wtforms.validators import DataRequired

ALLOWED_EXTENSIONS = ['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png']

class VerificationUploadForm(FlaskForm):
    document_type = SelectField('Document Type', validators=[DataRequired()], choices=[
        ('government_id', 'Government ID'),
        ('business_permit', 'Business Permit'),
        ('professional_license', 'Professional License'),
        ('resume', 'Resume/CV'),
        ('certification', 'Professional Certification'),
        ('other', 'Other Supporting Document')
    ])
    
    document = FileField('Document', validators=[
        FileRequired(),
        FileAllowed(ALLOWED_EXTENSIONS, 'Only PDF, DOC, DOCX, JPG, and PNG files are allowed!')
    ])

class VerificationReviewForm(FlaskForm):
    status = SelectField('Status', validators=[DataRequired()], choices=[
        ('pending', 'Pending Review'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected')
    ])
    notes = TextAreaField('Review Notes')