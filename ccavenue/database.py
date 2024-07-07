from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


# Invoice model
class PaymentInvoice(db.Model):
    __tablename__ = 'PaymentInvoice'

    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.String(100), nullable=True)
    invoice_status = db.Column(db.String(255), nullable=True)
    merchant_reference_no = db.Column(db.String(50), nullable=True)
    customer_name = db.Column(db.Text)
    customer_email_id = db.Column(db.Text)
    customer_mobile_no = db.Column(db.String(15))
    tiny_url = db.Column(db.String(255), nullable=True)
    error_code = db.Column(db.String(100), nullable=True)
    error_desc = db.Column(db.Text, nullable=True)
    status = db.Column(db.Boolean, default=False)
    status_text = db.Column(db.String(255), nullable=True)
    invoice_generate_time = db.Column(db.DateTime)


    def __repr__(self):
        return f"<PaymentInvoice {self.id}>"
    
# PaymentDetails model
class PaymentDetails(db.Model):
    __tablename__ = 'PaymentDetails'
    
    id = db.Column(db.Integer, primary_key = True)
    order_status = db.Column(db.String(100), nullable = True)
    order_amount = db.Column(db.String(100), nullable = True)
    order_no = db.Column(db.String(100), nullable = True)
    reference_no = db.Column(db.String(100), nullable = True)
    order_bill_name = db.Column(db.String(100), nullable = True)
    order_date_time = db.Column(db.String(100), nullable = True)
    payment_details = db.Column(db.JSON, nullable=True)
    data_request_time = db.Column(db.DateTime)


    def to_dict(self):
        return {
            'id': self.id,
            'order_status': self.order_status,
            'order_amount': self.order_amount,
            'order_no': self.order_no,
            'reference_no': self.reference_no,
            'order_bill_name': self.order_bill_name,
            'order_date_time': self.order_date_time,
            'payment_details': self.payment_details,
            'data_request_time': self.data_request_time
        }

    def __repr__(self):
        return f"<PaymentDetails(id={self.id}, order_no='{self.order_no}', order_status='{self.order_status}')>"

    
 # Define the Payment Invoice model
class RefundDetails(db.Model):
    __tablename__ = 'RefundDetails'

    id = db.Column(db.Integer, primary_key=True)
    reason = db.Column(db.String(100), nullable=True)
    error_code = db.Column(db.Integer, nullable=True)
    refund_status = db.Column(db.String(255), nullable=True)
    reference_no = db.Column(db.String(50), nullable=True)
    refund_amount = db.Column(db.Text, nullable=True)
    refund_ref_no = db.Column(db.String(100), nullable=True)
    refund_request_time = db.Column(db.DateTime)

    def __repr__(self):
        return f"<PaymentInvoice {self.id}>"
  