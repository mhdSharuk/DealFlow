from pydantic import BaseModel, Field

class EmailOutput(BaseModel):
    recipient_email: str = Field(description='Email address of the recipient')
    email_subject: str = Field(description='Subject line of the email')
    email_body: str = Field(description='Body content of the email with proper format')
    