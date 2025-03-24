from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
import os
from flask import send_from_directory
from werkzeug.utils import secure_filename
from datetime import datetime
import bcrypt


UPLOAD_FOLDER = 'documents'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

app=Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///household_service.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db=SQLAlchemy(app)

app.app_context().push()

class Admin(db.Model):
    __tablename__='admin'
    email=db.Column(db.String(100), nullable=False, primary_key=True)
    password=db.Column(db.String(100), nullable=False)

class ServiceProfessional(db.Model):
    __tablename__='service_professional'
    professional_id=db.Column(db.Integer, autoincrement=True, primary_key=True)
    email=db.Column(db.String(100), unique=True, nullable=False)
    password=db.Column(db.String(100), nullable=False)
    name=db.Column(db.String(100), nullable=False)
    contact=db.Column(db.Integer, nullable=False)
    city=db.Column(db.String(50), nullable=False)
    pincode=db.Column(db.Integer, nullable=False)
    registered_date = db.Column(db.DateTime, default=datetime.now)
    description = db.Column(db.String(200), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('service.service_id'),  nullable=False)
    experience = db.Column(db.Integer, nullable=False)
    document = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='Pending Approval')

    service_request = db.relationship('ServiceRequest', backref='service_professional', lazy='dynamic', primaryjoin='ServiceProfessional.professional_id==ServiceRequest.professional_id')
    review = db.relationship('Reviews', backref='service_professional', lazy='dynamic', primaryjoin='ServiceProfessional.professional_id==Reviews.professional_id')


class Customer(db.Model):
    __tablename__ = 'customer'
    customer_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    contact = db.Column(db.Integer, nullable=False)
    address = db.Column(db.String(200), nullable=False)
    pincode = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), default='Active')
    
    service_request = db.relationship('ServiceRequest', backref='customer', lazy='dynamic', primaryjoin='Customer.customer_id==ServiceRequest.customer_id')
    review = db.relationship('Reviews', backref='customer', lazy='dynamic', primaryjoin='Customer.customer_id==Reviews.customer_id')



class Service(db.Model):
    __tablename__ = 'service'
    service_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    min_price = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200), nullable=False)
    status=db.Column(db.String(50), default='Active')
    
    service_request = db.relationship('ServiceRequest', backref='service', lazy='dynamic', primaryjoin='Service.service_id==ServiceRequest.service_id')
    service_professional=db.relationship('ServiceProfessional', backref='service', lazy='select', primaryjoin='Service.service_id==ServiceProfessional.service_id')


class ServiceRequest(db.Model):
    __tablename__ = 'service_request'
    service_request_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('service.service_id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.customer_id'), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey('service_professional.professional_id'), nullable=False) 
    service_slot=db.Column(db.String(100), nullable=False)
    service_date=db.Column(db.Date, nullable=False)
    date_of_request = db.Column(db.DateTime, default=datetime.now)
    date_of_completion = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='Requested')
    remarks = db.Column(db.String(100), nullable=True)
    
    review = db.relationship('Reviews', backref='service_request', lazy='select', primaryjoin='ServiceRequest.service_request_id==Reviews.service_request_id')


class Reviews(db.Model):
    __tablename__ = 'reviews'
    review_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.customer_id'), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey('service_professional.professional_id'), nullable=False)
    service_request_id = db.Column(db.Integer, db.ForeignKey('service_request.service_request_id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment=db.Column(db.String(100), nullable=False)
    posted_datetime = db.Column(db.DateTime, default=datetime.now)    
    
@app.route("/admin/login", methods=['GET','POST'])
def admin_login():
    if request.method=='POST':
        email='n4nishantkumar2004@gmail.com'
        password=request.form['password']
        bytes=password.encode('utf-8')
        admin=Admin.query.filter_by(email=email).first()
        actual_password=admin.password
        status=bcrypt.checkpw(bytes,actual_password)
        if status==True:
            return redirect(url_for('admin_home'))
        else:
            return redirect(url_for('error',error='Wrong username or password'))
    else:
        return render_template("login_&_registration.html")


@app.route("/", methods=['POST', 'GET'])
def login():
    services=Service.query.all()
    
    if request.method=='POST':
        email=request.form['email']
        password=request.form['password']
        bytes=password.encode('utf-8')
        try:
            customer=Customer.query.filter_by(email=email).first()
            service_professional=ServiceProfessional.query.filter_by(email=email).first()
            if customer:
                customer_password=customer.password
                if bcrypt.checkpw(bytes, customer_password):
                    return redirect(url_for('customer_home', email=email))
                else:
                    return redirect(url_for('error', error='Wrong password'))
            elif service_professional:
                service_professional_password=service_professional.password
                if bcrypt.checkpw(bytes, service_professional_password):
                    return redirect(url_for('service_professional_home', email=email))
                else:
                    return redirect(url_for('error', error='Wrong password'))
            else:
                return redirect(url_for('error', error='There is no user from this email.'))
                
        except:
            return redirect(url_for('error', error='Something going wrong.'))
            
        
    else:    
        return render_template("login_&_registration.html", services=services)

@app.route("/customer/registration", methods=['GET', 'POST'])
def customer_registration():
    if request.method=='POST':
        email=request.form['customeremail']
        password=request.form['customerpassword']
        name=request.form['customername']
        contact=request.form['customer_contact']
        address=request.form['customeraddress']
        pincode=request.form['pincode']
        bytes=password.encode('utf-8')
        salt=bcrypt.gensalt()
        secured_password=bcrypt.hashpw(bytes,salt)
        
        service_professional=ServiceProfessional.query.filter_by(email=email).first()
        if service_professional is not None:
            return redirect(url_for('error', error="Email ID exists as a Service Professional."))
        else:
            new_customer=Customer(email=email, password=secured_password, name=name, contact=contact, address=address, pincode=pincode)
        try:
            db.session.add(new_customer)
            db.session.commit()
            return redirect(url_for('registered', name=name))
        except:
            return redirect(url_for('error', error="Email ID exists."))


@app.route("/customer/home/<email>", methods=['GET'])
def customer_home(email):
    customer=Customer.query.filter_by(email=email).first()
    services=Service.query.all()
    service_with_professional=[]
    for service in services:
        service_professional=ServiceProfessional.query.filter_by(service_id=service.service_id, status='Verified').all()
        professional_with_review=[]
        for professional in service_professional:
            reviews=Reviews.query.filter_by(professional_id=professional.professional_id).all()
            avg_rating = cal_avg_rating(professional.professional_id)
            professional_with_review.append({'professional':professional, 'reviews':reviews, 'avg_rating':avg_rating})
        
        service_with_professional.append({'service':service, 'service_professional':professional_with_review})
    
    service_requests=ServiceRequest.query.filter_by(customer_id=customer.customer_id).all()
    requests=[]
    for service_request in service_requests:
        this_service=Service.query.filter_by(service_id=service_request.service_id).first()
        this_professional=ServiceProfessional.query.filter_by(professional_id=service_request.professional_id).first()
        review=Reviews.query.filter_by(service_request_id=service_request.service_request_id).first()
        requests.append({'request_id':service_request,'this_service':this_service, 'this_professional':this_professional, 'review':review})
    
    return render_template('customer_home.html', customer=customer, service_with_professional=service_with_professional, requests=requests)
    

@app.route("/customer/edit/service/<int:service_request_id>", methods=['POST'])
def customer_edit_service(service_request_id):
    try:
        service_request=ServiceRequest.query.filter_by(service_request_id=service_request_id).first()
        service_request.service_slot=request.form['slot']
        service_date_str=request.form['service_date']
        service_request.service_date=datetime.strptime(service_date_str, '%Y-%m-%d').date()
        service_request.remarks=request.form['remarks']
        
        db.session.commit()
        customer=Customer.query.filter_by(customer_id=service_request.customer_id).first()
        return redirect(url_for('customer_home', email=customer.email))
    except:
        return redirect(url_for('error', error='Editing failed! try again.'))
    

@app.route("/service/book_1/<int:customer_id>/<int:service_id>/<int:professional_id>", methods=['POST'])
def service_book_1(customer_id, service_id, professional_id):
    customer=Customer.query.filter_by(customer_id=customer_id).first()
    service_slot=request.form['slot']
    service_date_str=request.form['service_date']
    service_date=datetime.strptime(service_date_str, '%Y-%m-%d').date()
    remarks=request.form['remarks']
    new_request = ServiceRequest(service_id=service_id, customer_id=customer_id, professional_id=professional_id, service_slot=service_slot, service_date=service_date, status='Requested', remarks=remarks)
    try:
        db.session.add(new_request)
        db.session.commit()
        return redirect(url_for('customer_home', email=customer.email))
    except:
        return redirect(url_for('error', error='Service Request not added'))

@app.route("/service/book_2/<int:customer_id>/<int:service_id>/<int:professional_id>", methods=['POST'])
def service_book_2(customer_id, service_id, professional_id):
    customer=Customer.query.filter_by(customer_id=customer_id).first()
    service_slot=request.form['slot']
    service_date_str=request.form['service_date']
    service_date=datetime.strptime(service_date_str, '%Y-%m-%d').date()
    remarks=request.form['remarks']
    new_request = ServiceRequest(service_id=service_id, customer_id=customer_id, professional_id=professional_id, service_slot=service_slot, service_date=service_date, status='Requested', remarks=remarks)
    try:
        db.session.add(new_request)
        db.session.commit()
        return redirect(url_for('customer_search', email=customer.email))
    except:
        return redirect(url_for('error', error='Service Request not added'))


@app.route("/service/withdraw/<int:service_request_id>")
def service_withdraw(service_request_id):
    service_request=ServiceRequest.query.filter_by(service_request_id=service_request_id).first()
    customer=Customer.query.filter_by(customer_id=service_request.customer_id).first()
    
    service_request.status='Withdraw'
    db.session.commit()
    return redirect(url_for('customer_home', email=customer.email))

@app.route("/service/review/<int:customer_id>/<int:professional_id>/<int:service_request_id>", methods=['POST'])
def service_review(customer_id, professional_id, service_request_id):
    customer=Customer.query.filter_by(customer_id=customer_id).first()
    service_request=ServiceRequest.query.filter_by(service_request_id=service_request_id).first()
    if request.method=='POST':
        rating=request.form['rating']
        comment=request.form['comment']
        new_review=Reviews(customer_id=customer_id, professional_id=professional_id, service_request_id=service_request_id, rating=rating, comment=comment)
        try:
            db.session.add(new_review)
            if service_request.date_of_completion is None:
                service_request.date_of_completion=datetime.now()
            service_request.status='Closed'
            db.session.commit()
            return redirect(url_for('customer_home', email=customer.email))
        except:
            return redirect(url_for('error', error='Review not added'))

@app.route("/customer/edit_1/profile/<int:customer_id>", methods=['POST'])
def customer_edit_1_profile(customer_id):
    try:
        customer=Customer.query.filter_by(customer_id=customer_id).first()
        customer.name=request.form['customername']
        customer.email=request.form['customeremail']
        customer.contact=request.form['customer_contact']
        customer.address=request.form['customeraddress']
        customer.pincode=request.form['pincode']

        service_professional=ServiceProfessional.query.filter_by(email=customer.email).first()
        if service_professional is not None:
            return redirect(url_for('error', error="Email ID exists as a Service Professional."))
        db.session.commit()
        return redirect(url_for('customer_home', email=customer.email))
    except:
        return redirect(url_for('error', error='Email ID already exists.'))

@app.route("/customer/edit_2/profile/<int:customer_id>", methods=['POST'])
def customer_edit_2_profile(customer_id):
    try:
        customer=Customer.query.filter_by(customer_id=customer_id).first()
        customer.name=request.form['customername']
        customer.email=request.form['customeremail']
        customer.contact=request.form['customer_contact']
        customer.address=request.form['customeraddress']
        customer.pincode=request.form['pincode']
        
        service_professional=ServiceProfessional.query.filter_by(email=customer.email).first()
        if service_professional is not None:
            return redirect(url_for('error', error="Email ID exists as a Service Professional."))
        db.session.commit()
        return redirect(url_for('customer_search', email=customer.email))
    except:
        return redirect(url_for('error', error='Profile editing failed'))


def cal_avg_rating(professional_id):
    rating = 0
    count = 0
    reviews = Reviews.query.filter_by(professional_id=professional_id).all()
    for review in reviews:
        rating += review.rating
        count += 1
        
    if count==0:
        avg_rating=0
    else:
        avg_rating=round(rating / count, 2)
        
    return avg_rating



@app.route("/customer/search/<email>", methods=['GET','POST'])
def customer_search(email):
    customer=Customer.query.filter_by(email=email).first()
    
    type=request.args.get('type')
    
    if request.method=='POST':
        type=request.form['type']
        search=request.form['search']
        search_output='%' + search + '%'
        
        
        if type=='Service Name':
            services=Service.query.filter(Service.name.like(search_output)).all()
            service_with_professional=[]
            for service in services:
                service_professional=ServiceProfessional.query.filter_by(service_id=service.service_id, status='Verified').all()
                professional_with_review=[]
                for professional in service_professional:
                    reviews=Reviews.query.filter_by(professional_id=professional.professional_id).all()
                    avg_rating = cal_avg_rating(professional.professional_id)
                    professional_with_review.append({'professional':professional, 'reviews':reviews, 'avg_rating':avg_rating})
                        
                service_with_professional.append({'service':service, 'service_professional':professional_with_review})

            return render_template('customer_search.html', customer=customer, service_with_professional=service_with_professional, type=type)
        
        elif type=='Service Professional Name':
            service_professional=ServiceProfessional.query.filter(ServiceProfessional.status=='Verified', ServiceProfessional.name.like(search_output)).all()
            service_professional_output=[]
            for professional in service_professional:
                service=Service.query.filter_by(service_id=professional.service_id).first()
                reviews=Reviews.query.filter_by(professional_id=professional.professional_id).all()
                avg_rating = cal_avg_rating(professional.professional_id)
                
                service_professional_output.append({'professional':professional, 'service':service, 'reviews':reviews, 'avg_rating':avg_rating})
                    
                    
            return render_template('customer_search.html', customer=customer, service_professional_output=service_professional_output, type=type)
        
        elif type=='City':
            service_professional=ServiceProfessional.query.filter(ServiceProfessional.city.like(search_output)).all()
            service_professional_output=[]
            for professional in service_professional:
                service=Service.query.filter_by(service_id=professional.service_id).first()
                reviews=Reviews.query.filter_by(professional_id=professional.professional_id).all()
                avg_rating = cal_avg_rating(professional.professional_id)
                
                service_professional_output.append({'professional':professional, 'service':service, 'reviews':reviews, 'avg_rating':avg_rating})
                    
                    
            return render_template('customer_search.html', customer=customer, service_professional_output=service_professional_output, type=type)
        
        elif type=='Pincode':
            service_professional=ServiceProfessional.query.filter(ServiceProfessional.pincode.like(search_output)).all()
            service_professional_output=[]
            for professional in service_professional:
                service=Service.query.filter_by(service_id=professional.service_id).first()
                reviews=Reviews.query.filter_by(professional_id=professional.professional_id).all()
                avg_rating = cal_avg_rating(professional.professional_id)
                
                service_professional_output.append({'professional':professional, 'service':service, 'reviews':reviews, 'avg_rating':avg_rating})
                    
                    
            return render_template('customer_search.html', customer=customer, service_professional_output=service_professional_output, type=type)
        
        else:
            return redirect(url_for('error', error='Please select search type'))
        
    else:
        return render_template('customer_search.html', customer=customer, type=type)


@app.route('/customer/search/service/name/<email>')
def customer_search_service_name(email):
    customer=Customer.query.filter_by(email=email).first()
    return redirect(url_for('customer_search', email=customer.email, type='Service Name'))


@app.route('/customer/search/service/professional/name/<email>')
def customer_search_service_professional_name(email):
    customer=Customer.query.filter_by(email=email).first()
    return redirect(url_for('customer_search', email=customer.email, type='Service Professional Name'))


@app.route('/customer/search/city/<email>')
def customer_search_city(email):
    customer=Customer.query.filter_by(email=email).first()
    return redirect(url_for('customer_search', email=customer.email, type='City'))


@app.route('/customer/search/pincode/<email>')
def customer_search_pincode(email):
    customer=Customer.query.filter_by(email=email).first()
    return redirect(url_for('customer_search', email=customer.email, type='Pincode'))


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/service/professional/registration", methods=['GET', 'POST'])
def service_professional_registration():
    if request.method=='POST':
        email=request.form['service_professional_email']
        password=request.form['service_professional_password']
        name=request.form['service_professional_name']
        contact=request.form['service_professional_contact']
        city=request.form['service_professional_city']
        pincode=request.form['service_professional_pincode']
        description=request.form['description']
        service_id=request.form['service_id']
        experience=request.form['experience']
        document=request.files['document']
        bytes=password.encode('utf-8')
        salt=bcrypt.gensalt()
        secured_password=bcrypt.hashpw(bytes,salt)
        
        customer=Customer.query.filter_by(email=email).first()
        if customer is not None:
            return redirect(url_for('error', error="Email ID exists as a customer."))
        else:
            if document and allowed_file(document.filename):
                _, file_extension = os.path.splitext(document.filename)
                filename=secure_filename(email.split('@')[0]+file_extension)
                document.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                new_service_professional=ServiceProfessional(email=email, password=secured_password, name=name, contact=contact, city=city, pincode=pincode, description=description, service_id=service_id, experience=int(experience), document=filename)
        try:
            db.session.add(new_service_professional)
            db.session.commit()
            return redirect(url_for('registered', name=name))
        except:
            return redirect(url_for('error', error="Email ID exists."))


@app.route('/service/professional/home/<email>', methods=['GET'])
def service_professional_home(email):
    service_professional=ServiceProfessional.query.filter_by(email=email).first()
    service=Service.query.filter_by(service_id=service_professional.service_id).first()
    today_date=datetime.now()
    service_request=ServiceRequest.query.filter_by(professional_id=service_professional.professional_id).all()
    service_requests=[]
    service_professional_rating = cal_avg_rating(service_professional.professional_id)
                
    for request in service_request:
        customer=Customer.query.filter_by(customer_id=request.customer_id).first()
        review=Reviews.query.filter_by(service_request_id=request.service_request_id).first()
        service_requests.append({'request':request, 'customer':customer, 'review':review})
        
        
    return render_template('service_professional_home.html', service_professional=service_professional, service=service, today_date=today_date, service_requests=service_requests, service_professional_rating=service_professional_rating)



@app.route('/service/professional/accept_1/<int:service_request_id>')
def service_professional_accept_1(service_request_id):
    service_request=ServiceRequest.query.filter_by(service_request_id=service_request_id).first()
    service_professional=ServiceProfessional.query.filter_by(professional_id=service_request.professional_id).first()
    
    service_request.status='Accepted'
    db.session.commit()
    return redirect(url_for('service_professional_home', email=service_professional.email))

@app.route('/service/professional/accept_2/<int:service_request_id>')
def service_professional_accept_2(service_request_id):
    service_request=ServiceRequest.query.filter_by(service_request_id=service_request_id).first()
    service_professional=ServiceProfessional.query.filter_by(professional_id=service_request.professional_id).first()
    
    service_request.status='Accepted'
    db.session.commit()
    return redirect(url_for('service_professional_search', email=service_professional.email))


@app.route('/service/professional/reject_1/<int:service_request_id>')
def service_professional_reject_1(service_request_id):
    service_request=ServiceRequest.query.filter_by(service_request_id=service_request_id).first()
    service_professional=ServiceProfessional.query.filter_by(professional_id=service_request.professional_id).first()
    
    service_request.status='Rejected'
    db.session.commit()
    return redirect(url_for('service_professional_home', email=service_professional.email))

@app.route('/service/professional/reject_2/<int:service_request_id>')
def service_professional_reject_2(service_request_id):
    service_request=ServiceRequest.query.filter_by(service_request_id=service_request_id).first()
    service_professional=ServiceProfessional.query.filter_by(professional_id=service_request.professional_id).first()
    
    service_request.status='Rejected'
    db.session.commit()
    return redirect(url_for('service_professional_search', email=service_professional.email))


@app.route('/service/professional/close_1/<int:service_request_id>')
def service_professional_close_1(service_request_id):
    service_request=ServiceRequest.query.filter_by(service_request_id=service_request_id).first()
    service_professional=ServiceProfessional.query.filter_by(professional_id=service_request.professional_id).first()
    
    if service_request.date_of_completion is None:
        service_request.date_of_completion=datetime.now()
    service_request.status='Service Professional Closed'
    db.session.commit()
    return redirect(url_for('service_professional_home', email=service_professional.email))

@app.route('/service/professional/close_2/<int:service_request_id>')
def service_professional_close_2(service_request_id):
    service_request=ServiceRequest.query.filter_by(service_request_id=service_request_id).first()
    service_professional=ServiceProfessional.query.filter_by(professional_id=service_request.professional_id).first()
    
    if service_request.date_of_completion is None:
        service_request.date_of_completion=datetime.now()
    service_request.status='Service Professional Closed'
    db.session.commit()
    return redirect(url_for('service_professional_search', email=service_professional.email))



@app.route("/service/professional/edit_1/profile/<int:professional_id>", methods=['POST'])
def professional_edit_1_profile(professional_id):
    try:
        service_professional=ServiceProfessional.query.filter_by(professional_id=professional_id).first()
        service_professional.name=request.form['service_professional_name']
        service_professional.email=request.form['service_professional_email']
        service_professional.contact=request.form['service_professional_contact']
        service_professional.city=request.form['service_professional_city']
        service_professional.pincode=request.form['service_professional_pincode']
        service_professional.experience=request.form['service_professional_experience']
        
        new_email=service_professional.email
        new_email_name=new_email.split('@')[0]
        
        document_folder=os.path.join(os.getcwd(), 'documents')
        old_image_path=os.path.join(document_folder, service_professional.document)
        extension=os.path.splitext(service_professional.document)[1]
        new_image_path=os.path.join(document_folder, new_email_name + extension)
        new_image_name=os.path.join(new_email_name + extension)
        os.rename(old_image_path, new_image_path)
        
        service_professional.document=new_image_name

        customer=Customer.query.filter_by(email=service_professional.email).first()
        if customer is not None:
            return redirect(url_for('error', error="Email ID exists as a Customer."))
        db.session.commit()
        return redirect(url_for('service_professional_home', email=service_professional.email))
    except:
        return redirect(url_for('error', error='Email ID already exists.'))


@app.route("/service/professional/edit_2/profile/<int:professional_id>", methods=['POST'])
def professional_edit_2_profile(professional_id):
    try:
        service_professional=ServiceProfessional.query.filter_by(professional_id=professional_id).first()
        service_professional.name=request.form['service_professional_name']
        service_professional.email=request.form['service_professional_email']
        service_professional.contact=request.form['service_professional_contact']
        service_professional.city=request.form['service_professional_city']
        service_professional.pincode=request.form['service_professional_pincode']
        service_professional.experience=request.form['service_professional_experience']

        customer=Customer.query.filter_by(email=service_professional.email).first()
        if customer is not None:
            return redirect(url_for('error', error="Email ID exists as a Customer."))
        db.session.commit()
        return redirect(url_for('service_professional_search', email=service_professional.email))
    except:
        return redirect(url_for('error', error='Email ID already exists.'))



@app.route('/service/professional/search/<email>', methods=['GET', 'POST'])
def service_professional_search(email):
    service_professional=ServiceProfessional.query.filter_by(email=email).first()
    service=Service.query.filter_by(service_id=service_professional.service_id).first()
    reviews=Reviews.query.filter_by(professional_id=service_professional.professional_id).all()
    service_professional_rating = cal_avg_rating(service_professional.professional_id)
    
    type = request.args.get('type')
    
    if request.method=='POST':
        type=request.form['type']
        search=request.form['search']
        search_output='%' + search + '%'
        
        customers = ServiceRequest.query.outerjoin(Customer, ServiceRequest.customer_id == Customer.customer_id).filter(ServiceRequest.professional_id == service_professional.professional_id)

        
        if type=='Customer Name':
            customer_outputs=customers.filter(Customer.name.like(search_output)).all()
            
            return render_template('service_professional_search.html', email=service_professional.email, service_professional=service_professional, service=service, service_professional_rating=service_professional_rating, customer_outputs=customer_outputs, reviews=reviews, type=type)
        
        elif type=='Requested on':
            customer_outputs=customers.filter(ServiceRequest.date_of_request.like(search_output)).all()
            
            return render_template('service_professional_search.html', email=service_professional.email, service_professional=service_professional, service=service, service_professional_rating=service_professional_rating, customer_outputs=customer_outputs, reviews=reviews, type=type)
        
        elif type=='Requested for':
            customer_outputs=customers.filter(ServiceRequest.service_date.like(search_output)).all()
            
            return render_template('service_professional_search.html', email=service_professional.email, service_professional=service_professional, service=service, service_professional_rating=service_professional_rating, customer_outputs=customer_outputs, reviews=reviews, type=type)
        
        elif type=='Completed on':
            customer_outputs=customers.filter(ServiceRequest.date_of_completion.like(search_output)).all()
            
            return render_template('service_professional_search.html', email=service_professional.email, service_professional=service_professional, service=service, service_professional_rating=service_professional_rating, customer_outputs=customer_outputs, reviews=reviews, type=type)
        
        elif type=='Address':
            customer_outputs=customers.filter(Customer.address.like(search_output)).all()
            
            return render_template('service_professional_search.html', email=service_professional.email, service_professional=service_professional, service=service, service_professional_rating=service_professional_rating, customer_outputs=customer_outputs, reviews=reviews, type=type)
        
        elif type=='Pincode':
            customer_outputs=customers.filter(Customer.pincode.like(search_output)).all()
            
            return render_template('service_professional_search.html', email=service_professional.email, service_professional=service_professional, service=service, service_professional_rating=service_professional_rating, customer_outputs=customer_outputs, reviews=reviews, type=type)
        
        else:
            return redirect(url_for('error', error='Please select search type'))
        
    else:
        return render_template('service_professional_search.html', email=service_professional.email, service_professional=service_professional, service=service, service_professional_rating=service_professional_rating, type=type)


@app.route('/service_professional/search/customer/name/<email>')
def service_professional_search_customer_name(email):
    service_professional=ServiceProfessional.query.filter_by(email=email).first()
    return redirect(url_for('service_professional_search', email=service_professional.email, type='Customer Name'))


@app.route('/service_professional/search/requested/date/<email>')
def service_professional_search_requested_date(email):
    service_professional=ServiceProfessional.query.filter_by(email=email).first()
    return redirect(url_for('service_professional_search', email=service_professional.email, type='Requested on'))

@app.route('/service_professional/search/requested/date/for/<email>')
def service_professional_search_requested_date_for(email):
    service_professional=ServiceProfessional.query.filter_by(email=email).first()
    return redirect(url_for('service_professional_search', email=service_professional.email, type='Requested for'))


@app.route('/service_professional/search/completed/date/<email>')
def service_professional_search_completion_date(email):
    service_professional=ServiceProfessional.query.filter_by(email=email).first()
    return redirect(url_for('service_professional_search', email=service_professional.email, type='Completed on'))


@app.route('/service_professional/search/address/<email>')
def service_professional_search_address(email):
    service_professional=ServiceProfessional.query.filter_by(email=email).first()
    return redirect(url_for('service_professional_search', email=service_professional.email, type='Address'))

@app.route('/service_professional/search/pincode/<email>')
def service_professional_search_pincode(email):
    service_professional=ServiceProfessional.query.filter_by(email=email).first()
    return redirect(url_for('service_professional_search', email=service_professional.email, type='Pincode'))


@app.route('/admin/home', methods=['GET'])
def admin_home():
    services=Service.query.all()
    service_professionals=ServiceProfessional.query.filter(ServiceProfessional.status!='Rejected', ServiceProfessional.status!='Pending Approval',).all()
    service_professional_requests = ServiceProfessional.query.filter(or_(ServiceProfessional.status == 'Pending Approval', ServiceProfessional.status == 'Rejected')).all()
    service_professional_request=[]
    for professional in service_professional_requests:
        service=Service.query.filter_by(service_id=professional.service_id).first()
        service_professional_request.append({'professional':professional, 'service':service})
    professional_with_review=[]
    for professional in service_professionals:
        service=Service.query.filter_by(service_id=professional.service_id).first()
        reviews=Reviews.query.filter_by(professional_id=professional.professional_id).all()
        avg_rating = cal_avg_rating(professional.professional_id)
        professional_with_review.append({'professional':professional, 'service':service, 'reviews':reviews, 'avg_rating':avg_rating})
        
    customerss=Customer.query.all()
    customers=[]
    for customer in customerss:
        active_service=ServiceRequest.query.filter_by(customer_id=customer.customer_id, status='Accepted').count()
        customers.append({'customer':customer, 'active_service':active_service})
        
    ongoing_service_requests=ServiceRequest.query.filter(or_(ServiceRequest.status=='Accepted', ServiceRequest.status=='Requested')).all()
    ongoing_requests=[]
    for service_request in ongoing_service_requests:
        service=Service.query.filter_by(service_id=service_request.service_id).first()
        professional=ServiceProfessional.query.filter_by(professional_id=service_request.professional_id).first()
        customer=Customer.query.filter_by(customer_id=service_request.customer_id).first()
        ongoing_requests.append({'service':service, 'professional':professional, 'customer':customer, 'service_request':service_request})
    
    cancel_service_requests=ServiceRequest.query.filter(or_(ServiceRequest.status=='Rejected', ServiceRequest.status=='Withdraw')).all()
    cancel_requests=[]
    for service_request in cancel_service_requests:
        service=Service.query.filter_by(service_id=service_request.service_id).first()
        professional=ServiceProfessional.query.filter_by(professional_id=service_request.professional_id).first()
        customer=Customer.query.filter_by(customer_id=service_request.customer_id).first()
        cancel_requests.append({'service':service, 'professional':professional, 'customer':customer, 'service_request':service_request})
        
    closed_service_requests=ServiceRequest.query.filter(or_(ServiceRequest.status=='Closed', ServiceRequest.status=='Service Professional Closed')).all()
    closed_requests=[]
    for service_request in closed_service_requests:
        service=Service.query.filter_by(service_id=service_request.service_id).first()
        professional=ServiceProfessional.query.filter_by(professional_id=service_request.professional_id).first()
        customer=Customer.query.filter_by(customer_id=service_request.customer_id).first()
        review=Reviews.query.filter_by(service_request_id=service_request.service_request_id).first()
        closed_requests.append({'service':service, 'professional':professional, 'customer':customer, 'review':review, 'service_request':service_request})
        
    
    return render_template('admin_home.html', service_professional_request=service_professional_request, services=services, professional_with_review=professional_with_review, customers=customers, ongoing_requests=ongoing_requests, cancel_requests=cancel_requests, closed_requests=closed_requests)


@app.route('/service/professional/document/<document>')
def service_professional_document(document):
    return send_from_directory(app.config["UPLOAD_FOLDER"], document)

@app.route('/admin/add/service', methods=['POST'])
def admin_add_service():
    try:
        service_name=request.form['service_name']
        service_min_price=request.form['service_min_price']
        service_description=request.form['service_description']
        new_service=Service(name=service_name, min_price=service_min_price, description=service_description)
        db.session.add(new_service)
        db.session.commit()
        return redirect(url_for('admin_home'))
    except:
        return redirect(url_for('error', error='Could not add Service, Something going wrong.'))


@app.route('/admin/edit_1/service/<int:service_id>', methods=['POST'])
def admin_edit_1_service(service_id):
    try:
        service=Service.query.filter_by(service_id=service_id).first()
        service.min_price=request.form['edit_service_min_price']
        service.description=request.form['edit_service_description']
        db.session.commit()
        return redirect(url_for('admin_home'))
    except:
        return redirect(url_for('error',  error='Could not edit Service, Something going wrong.'))
    
@app.route('/admin/edit_2/service/<int:service_id>', methods=['POST'])
def admin_edit_2_service(service_id):
    try:
        service=Service.query.filter_by(service_id=service_id).first()
        service.min_price=request.form['edit_service_min_price']
        service.description=request.form['edit_service_description']
        db.session.commit()
        return redirect(url_for('admin_search'))
    except:
        return redirect(url_for('error',  error='Could not edit Service, Something going wrong.'))
    

@app.route('/admin/service/deactivate_1/<int:service_id>')
def service_deactivate_1(service_id):
    try:
        service=Service.query.filter_by(service_id=service_id).first()
        service.status='Inactive'
        db.session.commit()
        return redirect(url_for('admin_home'))
    except:
        return redirect(url_for('error',  error='Could not Deactivate Service, Something going wrong.'))


@app.route('/admin/service/deactivate_2/<int:service_id>')
def service_deactivate_2(service_id):
    try:
        service=Service.query.filter_by(service_id=service_id).first()
        service.status='Inactive'
        db.session.commit()
        return redirect(url_for('admin_search'))
    except:
        return redirect(url_for('error',  error='Could not Deactivate Service, Something going wrong.'))
    

@app.route('/admin/service/activate_1/<int:service_id>')
def service_activate_1(service_id):
    try:
        service=Service.query.filter_by(service_id=service_id).first()
        service.status='Active'
        db.session.commit()
        return redirect(url_for('admin_home'))
    except:
        return redirect(url_for('error',  error='Could not Activate Service, Something going wrong.'))
    
@app.route('/admin/service/activate_2/<int:service_id>')
def service_activate_2(service_id):
    try:
        service=Service.query.filter_by(service_id=service_id).first()
        service.status='Active'
        db.session.commit()
        return redirect(url_for('admin_search'))
    except:
        return redirect(url_for('error',  error='Could not Activate Service, Something going wrong.'))
    

@app.route('/admin/professional/accept/<int:professional_id>')
def professional_accept(professional_id):
    try:
        professional=ServiceProfessional.query.filter_by(professional_id=professional_id).first()
        professional.status='Verified'
        db.session.commit()
        return redirect(url_for('admin_home'))
    except:
        return redirect(url_for('error', error='Error in Approving.'))
    
@app.route('/admin/professional/accept_2/<int:professional_id>')
def professional_accept_2(professional_id):
    try:
        professional=ServiceProfessional.query.filter_by(professional_id=professional_id).first()
        professional.status='Verified'
        db.session.commit()
        return redirect(url_for('admin_search'))
    except:
        return redirect(url_for('error', error='Error in Approving.'))
    

@app.route('/admin/professional/reject/<int:professional_id>')
def professional_reject(professional_id):
    try:
        professional=ServiceProfessional.query.filter_by(professional_id=professional_id).first()
        professional.status='Rejected'
        db.session.commit()
        return redirect(url_for('admin_home'))
    except:
        return redirect(url_for('error', error='Error in Rejecting.'))

@app.route('/admin/professional/reject_2/<int:professional_id>')
def professional_reject_2(professional_id):
    try:
        professional=ServiceProfessional.query.filter_by(professional_id=professional_id).first()
        professional.status='Rejected'
        db.session.commit()
        return redirect(url_for('admin_search'))
    except:
        return redirect(url_for('error', error='Error in Rejecting.'))


@app.route('/admin/professional/block/<int:professional_id>')
def professional_block(professional_id):
    try:
        professional=ServiceProfessional.query.filter_by(professional_id=professional_id).first()
        professional.status='Blocked'
        db.session.commit()
        return redirect(url_for('admin_home'))
    except:
        return redirect(url_for('error', error='Error in Blocking.'))

@app.route('/admin/professional/block_2/<int:professional_id>')
def professional_block_2(professional_id):
    try:
        professional=ServiceProfessional.query.filter_by(professional_id=professional_id).first()
        professional.status='Blocked'
        db.session.commit()
        return redirect(url_for('admin_search'))
    except:
        return redirect(url_for('error', error='Error in Blocking.'))


@app.route('/admin/professional/unblock/<int:professional_id>')
def professional_unblock(professional_id):
    try:
        professional=ServiceProfessional.query.filter_by(professional_id=professional_id).first()
        professional.status='Verified'
        db.session.commit()
        return redirect(url_for('admin_home'))
    except:
        return redirect(url_for('error', error='Error in Unblocking.'))

@app.route('/admin/professional/unblock_2/<int:professional_id>')
def professional_unblock_2(professional_id):
    try:
        professional=ServiceProfessional.query.filter_by(professional_id=professional_id).first()
        professional.status='Verified'
        db.session.commit()
        return redirect(url_for('admin_search'))
    except:
        return redirect(url_for('error', error='Error in Unblocking.'))


@app.route('/admin/customer/block/<int:customer_id>')
def customer_block_1(customer_id):
    try:
        customer=Customer.query.filter_by(customer_id=customer_id).first()
        customer.status='Blocked'
        db.session.commit()
        return redirect(url_for('admin_home'))
    except:
        return redirect(url_for('error', error='Error in Blocking.'))

@app.route('/admin/customer/block_2/<int:customer_id>')
def customer_block_2(customer_id):
    try:
        customer=Customer.query.filter_by(customer_id=customer_id).first()
        customer.status='Blocked'
        db.session.commit()
        return redirect(url_for('admin_search'))
    except:
        return redirect(url_for('error', error='Error in Blocking.'))


@app.route('/admin/customer/unblock/<int:customer_id>')
def customer_unblock_1(customer_id):
    try:
        customer=Customer.query.filter_by(customer_id=customer_id).first()
        customer.status='Active'
        db.session.commit()
        return redirect(url_for('admin_home'))
    except:
        return redirect(url_for('error', error='Error in Unblocking.'))

@app.route('/admin/customer/unblock_2/<int:customer_id>')
def customer_unblock_2(customer_id):
    try:
        customer=Customer.query.filter_by(customer_id=customer_id).first()
        customer.status='Active'
        db.session.commit()
        return redirect(url_for('admin_search'))
    except:
        return redirect(url_for('error', error='Error in Unblocking.'))


@app.route('/admin/search', methods=['GET', 'POST'])
def admin_search():
    type=request.args.get('type')
    
    if request.method=='POST':
        type=request.form['type']
        search=request.form['search']
        search_output='%' + search + '%'
        
        
        if type=='Service Name':
            admin_search_outputs_service=Service.query.filter(Service.name.like(search_output)).all()
            return render_template('admin_search.html', admin_search_outputs_service=admin_search_outputs_service, type=type)
        
        elif type=='Customer Name':
            admin_search_outputs_customers=Customer.query.filter(Customer.name.like(search_output)).all()
            admin_search_outputs_customer=[]
            for output in admin_search_outputs_customers:
                active_service=ServiceRequest.query.filter_by(customer_id=output.customer_id, status='Accepted').count()
                admin_search_outputs_customer.append({'customer':output, 'active_service':active_service})
            return render_template('admin_search.html', admin_search_outputs_customer=admin_search_outputs_customer, type=type)
        
        
        elif type=='Service Professional Name':
            admin_search_outputs_professionals=ServiceProfessional.query.filter(ServiceProfessional.name.like(search_output)).all()
            admin_search_outputs_professional=[]
            for output in admin_search_outputs_professionals:
                service=Service.query.filter_by(service_id=output.service_id).first()
                reviews=Reviews.query.filter_by(professional_id=output.professional_id).all()
                avg_rating = cal_avg_rating(output.professional_id)
                admin_search_outputs_professional.append({'professional':output, 'service':service, 'reviews':reviews, 'avg_rating':avg_rating})
            return render_template('admin_search.html', admin_search_outputs_professional=admin_search_outputs_professional, type=type)
        
        elif type=='City/Address':
            search_customer_address=[]
            admin_search_outputs_customer_address=Customer.query.filter(Customer.address.like(search_output)).all()
            for customer in admin_search_outputs_customer_address:
                active_service=ServiceRequest.query.filter_by(customer_id=customer.customer_id, status='Accepted').count()
                search_customer_address.append({'customer':customer, 'active_service':active_service})
            search_professional_address=[]
            admin_search_outputs_professional_city=ServiceProfessional.query.filter(ServiceProfessional.city.like(search_output)).all()
            for professional in admin_search_outputs_professional_city:
                service=Service.query.filter_by(service_id=professional.service_id).first()
                reviews=Reviews.query.filter_by(professional_id=professional.professional_id).all()
                avg_rating = cal_avg_rating(professional.professional_id)
                search_professional_address.append({'professional':professional, 'service':service, 'reviews':reviews, 'avg_rating':avg_rating})
            return render_template('admin_search.html', admin_search_outputs_customer=search_customer_address, admin_search_outputs_professional=search_professional_address, type=type)
        
        elif type=='Pincode':
            search_customer_pincode=[]
            admin_search_outputs_customer_address=Customer.query.filter(Customer.pincode.like(search_output)).all()
            for customer in admin_search_outputs_customer_address:
                active_service=ServiceRequest.query.filter_by(customer_id=customer.customer_id, status='Accepted').count()
                search_customer_pincode.append({'customer':customer, 'active_service':active_service})
            search_professional_pincode=[]
            admin_search_outputs_professional_city=ServiceProfessional.query.filter(ServiceProfessional.pincode.like(search_output)).all()
            for professional in admin_search_outputs_professional_city:
                service=Service.query.filter_by(service_id=professional.service_id).first()
                reviews=Reviews.query.filter_by(professional_id=professional.professional_id).all()
                avg_rating = cal_avg_rating(professional.professional_id)
                search_professional_pincode.append({'professional':professional, 'service':service, 'reviews':reviews, 'avg_rating':avg_rating})
            return render_template('admin_search.html', admin_search_outputs_customer=search_customer_pincode, admin_search_outputs_professional=search_professional_pincode, type=type)
        
        elif type=='Requested on' or type=='Requested for' or type=='Completed on':
            service_datas=[]
            if type=='Requested on':
                service_datas=ServiceRequest.query.filter(ServiceRequest.date_of_request.like(search_output)).all()
            elif type=='Requested for':
                service_datas=ServiceRequest.query.filter(ServiceRequest.service_date.like(search_output)).all()
            elif type=='Completed on':
                service_datas=ServiceRequest.query.filter(ServiceRequest.date_of_completion.like(search_output)).all()
            
            service_data=[]
            for service_request in service_datas:
                service=Service.query.filter_by(service_id=service_request.service_id).first()
                professional=ServiceProfessional.query.filter_by(professional_id=service_request.professional_id).first()
                customer=Customer.query.filter_by(customer_id=service_request.customer_id).first()
                review=Reviews.query.filter_by(service_request_id=service_request.service_request_id).first()
                service_data.append({'service':service, 'professional':professional, 'customer':customer, 'review':review, 'service_request':service_request})
            return render_template('admin_search.html', service_data=service_data, search=search, type=type)
        
        else:
            return redirect(url_for('error', error='Please select search type'))
        
    else:
        return render_template('admin_search.html', type=type)


@app.route('/admin/search/service/name')
def admin_search_service_name():
    return redirect(url_for('admin_search', type='Service Name'))


@app.route('/admin/search/customer/name')
def admin_search_customer_name():
    return redirect(url_for('admin_search', type='Customer Name'))


@app.route('/admin/search/service/professional/name')
def admin_search_service_professional_name():
    return redirect(url_for('admin_search', type='Service Professional Name'))


@app.route('/admin/search/city_address')
def admin_search_city():
    return redirect(url_for('admin_search', type='City/Address'))


@app.route('/admin/search/pincode')
def admin_search_pincode():
    return redirect(url_for('admin_search', type='Pincode'))


@app.route('/admin/search/requested/date')
def admin_search_requested_date():
    return redirect(url_for('admin_search', type='Requested on'))


@app.route('/admin/search/requested/date/for')
def admin_search_requested_date_for():
    return redirect(url_for('admin_search', type='Requested for'))


@app.route('/admin/search/completed/date')
def admin_search_completed_date():
    return redirect(url_for('admin_search', type='Completed on'))


@app.route('/registered/<name>', methods=['GET'])
def registered(name):
    return render_template("registered.html", name=name)



@app.route('/error/<error>', methods=['GET'])
def error(error):
    return render_template("error.html", error=error)



if __name__ == "__main__":
    app.run(debug=True)