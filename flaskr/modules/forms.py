from flask_wtf import FlaskForm 
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import Optional, Length

class ArtworkForm(FlaskForm):
    title = StringField("Title", validators=[Optional(), Length(max=256)])
    description = TextAreaField("Description", validators=[Optional(), Length(max=1024)])
    submit = SubmitField("Submit")
