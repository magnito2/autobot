'use strict';

var _createClass = function () { function defineProperties(target, props) { for (var i = 0; i < props.length; i++) { var descriptor = props[i]; descriptor.enumerable = descriptor.enumerable || false; descriptor.configurable = true; if ("value" in descriptor) descriptor.writable = true; Object.defineProperty(target, descriptor.key, descriptor); } } return function (Constructor, protoProps, staticProps) { if (protoProps) defineProperties(Constructor.prototype, protoProps); if (staticProps) defineProperties(Constructor, staticProps); return Constructor; }; }();

function _defineProperty(obj, key, value) { if (key in obj) { Object.defineProperty(obj, key, { value: value, enumerable: true, configurable: true, writable: true }); } else { obj[key] = value; } return obj; }

function _classCallCheck(instance, Constructor) { if (!(instance instanceof Constructor)) { throw new TypeError("Cannot call a class as a function"); } }

function _possibleConstructorReturn(self, call) { if (!self) { throw new ReferenceError("this hasn't been initialised - super() hasn't been called"); } return call && (typeof call === "object" || typeof call === "function") ? call : self; }

function _inherits(subClass, superClass) { if (typeof superClass !== "function" && superClass !== null) { throw new TypeError("Super expression must either be null or a function, not " + typeof superClass); } subClass.prototype = Object.create(superClass && superClass.prototype, { constructor: { value: subClass, enumerable: false, writable: true, configurable: true } }); if (superClass) Object.setPrototypeOf ? Object.setPrototypeOf(subClass, superClass) : subClass.__proto__ = superClass; }

function SendMessage(props) {
    return React.createElement(
        'div',
        { id: 'sendmessage', style: { display: props.display ? 'block' : 'none' } },
        'Your message has been sent. Thank you!'
    );
}

function ErrorMessage(props) {
    return React.createElement(
        'div',
        { id: 'errormessage', style: { display: props.display ? 'block' : 'none' } },
        props.msg
    );
}

var FeedbackForm = function (_React$Component) {
    _inherits(FeedbackForm, _React$Component);

    function FeedbackForm(props) {
        _classCallCheck(this, FeedbackForm);

        var _this = _possibleConstructorReturn(this, (FeedbackForm.__proto__ || Object.getPrototypeOf(FeedbackForm)).call(this, props));

        _this.state = {
            name: '',
            email: '',
            subject: '',
            message: '',
            errors: {},
            was_success: false,
            resp_msg: '',
            resp_type: ''
        };
        _this.handleChange = _this.handleChange.bind(_this);
        _this.handleSubmit = _this.handleSubmit.bind(_this);
        return _this;
    }

    _createClass(FeedbackForm, [{
        key: 'handleChange',
        value: function handleChange(event) {
            var target = event.target;
            this.setState(_defineProperty({}, target.name, target.value));
        }
    }, {
        key: 'handleSubmit',
        value: function handleSubmit(event) {
            var _this2 = this;

            event.preventDefault();
            var req_data = {
                'name': this.state.name,
                'email': this.state.email,
                'subject': this.state.subject,
                'message': this.state.message
            };
            var responsePromise = fetch("/feedback", {
                method: "post",
                //cache: "no-cache",
                //mode: 'no-cors',
                //dataType: 'json',
                headers: {
                    //"Content-Type": "application/x-www-form-urlencoded",
                    "Content-Type": "application/json",
                    'X-CSRFToken': document.getElementById("csrf_token").value
                },
                //body: formData,
                body: JSON.stringify(req_data)
            });
            responsePromise.then(function (response) {
                if (response.ok) {
                    console.log("feedback form has been submitted");
                    response.text().then(function (data) {
                        //console.log("data recieved", data);
                        var jdata = JSON.parse(data);
                        $.notify({
                            message: jdata["msg"]
                        }, {
                            type: jdata["type"]
                        });
                        console.log('response received is ' + jdata['errors']);
                        //formEl.reset();
                        if (jdata['errors']) {
                            _this2.setState({ errors: jdata['errors'] });
                        } else {
                            console.log("didnt see the error comming");
                            _this2.setState({ was_success: true, errors: {} });
                        }
                        _this2.setState({ resp_msg: jdata['msg'], resp_type: jdata['type'] });
                    });
                } else {
                    response.text().then(function (data) {
                        console.log(data);
                    });
                }
            });
        }
    }, {
        key: 'render',
        value: function render() {
            console.log("and the resp msg is ", this.state.resp_msg);
            return React.createElement(
                'div',
                { 'class': 'form' },
                React.createElement(SendMessage, { display: this.state.was_success, msg: this.state.resp_msg }),
                React.createElement(ErrorMessage, { display: this.state.resp_type == "danger", msg: this.state.resp_msg }),
                React.createElement(
                    'form',
                    { role: 'form', 'class': 'contactForm', id: 'feedback-form', onSubmit: this.handleSubmit },
                    React.createElement('input', { id: 'csrf_token', type: 'hidden', name: 'csrf_token', value: '' }),
                    React.createElement(
                        'div',
                        { 'class': 'form-row' },
                        React.createElement(
                            'div',
                            { 'class': 'form-group col-lg-6 has-error has-feedback' },
                            React.createElement('input', { type: 'text', name: 'name', 'class': 'form-control', id: 'name', placeholder: 'Your Name', onChange: this.handleChange }),
                            React.createElement(
                                'div',
                                { 'class': 'validation' },
                                this.state.errors.name
                            )
                        ),
                        React.createElement(
                            'div',
                            { 'class': 'form-group col-lg-6' },
                            React.createElement('input', { type: 'email', 'class': 'form-control', name: 'email', id: 'email', placeholder: 'Your Email', onChange: this.handleChange }),
                            React.createElement(
                                'div',
                                { 'class': 'validation' },
                                this.state.errors.email
                            )
                        )
                    ),
                    React.createElement(
                        'div',
                        { 'class': 'form-group' },
                        React.createElement('input', { type: 'text', 'class': 'form-control', name: 'subject', id: 'subject', placeholder: 'Subject', onChange: this.handleChange }),
                        React.createElement('div', { 'class': 'validation' })
                    ),
                    React.createElement(
                        'div',
                        { 'class': 'form-group' },
                        React.createElement('textarea', { 'class': 'form-control', name: 'message', id: 'message', rows: '5', placeholder: 'Message', onChange: this.handleChange }),
                        React.createElement(
                            'div',
                            { 'class': 'validation' },
                            this.state.errors.message
                        )
                    ),
                    React.createElement(
                        'div',
                        { 'class': 'text-center' },
                        React.createElement(
                            'button',
                            { type: 'submit', title: 'Send Message' },
                            'Send Message'
                        )
                    )
                )
            );
        }
    }]);

    return FeedbackForm;
}(React.Component);

ReactDOM.render(React.createElement(FeedbackForm, null), document.getElementById("feedback-form"));