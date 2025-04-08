# routes/payment_routes.py
from flask import Blueprint, flash, redirect, url_for, request
import paypalrestsdk

payment_bp = Blueprint('payment', __name__)

@payment_bp.route('/create_payment')
def create_payment():
    amount = request.args.get('amount', default=10, type=int)
    payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {"payment_method": "paypal"},
        "redirect_urls": {
            "return_url": url_for('payment.paypal_success', _external=True),
            "cancel_url": url_for('payment.paypal_cancel', _external=True)
        },
        "transactions": [{
            "amount": {"total": str(amount), "currency": "USD"},
            "description": "Thanh toán đặt phòng khách sạn"
        }]
    })

    if payment.create():
        for link in payment.links:
            if link.rel == "approval_url":
                return redirect(link.href)
    else:
        return "Lỗi tạo thanh toán", 400

@payment_bp.route('/paypal_success')
def paypal_success():
    payment_id = request.args.get('paymentId')
    payer_id = request.args.get('PayerID')

    payment = paypalrestsdk.Payment.find(payment_id)

    if payment.execute({"payer_id": payer_id}):
        flash("Thanh toán thành công!", "success")
        return redirect(url_for('user.index'))
    else:
        return "Thanh toán thất bại", 400

@payment_bp.route('/paypal_cancel')
def paypal_cancel():
    flash("Thanh toán đã bị hủy!", "error")
    return redirect(url_for('user.index'))