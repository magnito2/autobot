function SendMessage(props) {
    return (
        <div id="sendmessage" style={{display: props.display ? 'block' : 'none' }}>Your message has been sent. Thank you!</div>
    )
}

function ErrorMessage(props) {
    return (
        <div id="errormessage" style={{display: props.display ? 'block' : 'none' }}>{props.msg}</div>
    )
}

class FeedbackForm extends React.Component {
    constructor(props){
        super(props);
        this.state = {
            name : '',
            email : '',
            subject : '',
            message : '',
            errors : {},
            was_success: false,
            resp_msg: '',
            resp_type: ''
        };
        this.handleChange = this.handleChange.bind(this);
        this.handleSubmit = this.handleSubmit.bind(this);
    }

    handleChange(event){
        const target = event.target;
        this.setState({
            [target.name] : target.value
        });
    }

    handleSubmit(event){
        event.preventDefault();
        const req_data = {
            'name' : this.state.name,
            'email' : this.state.email,
            'subject' : this.state.subject,
            'message' : this.state.message
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
        responsePromise.then(
            response => {
                if (response.ok) {
                    console.log("feedback form has been submitted");
                    response.text().then(data => {
                        //console.log("data recieved", data);
                        const jdata = JSON.parse(data);
                        $.notify({
                                message: jdata["msg"]
                            },
                            {
                                type: jdata["type"]
                            });
                        console.log(`response received is ${jdata['errors']}`);
                        //formEl.reset();
                        if (jdata['errors']){
                            this.setState({errors : jdata['errors']});
                        }else{
                            console.log("didnt see the error comming");
                            this.setState({ was_success: true, errors: {}})
                        }
                        this.setState({ resp_msg: jdata['msg'], resp_type: jdata['type']})

                    })
                }
                else {
                    response.text().then(data => {
                        console.log(data);
                    });
                }
            }
        );
    }

    render(){
        console.log("and the resp msg is ", this.state.resp_msg);
        return(
            <div class="form">
                <SendMessage display={this.state.was_success} msg={this.state.resp_msg}/>
                <ErrorMessage display={this.state.resp_type == "danger" } msg={this.state.resp_msg}/>
                <form role="form" class="contactForm" id="feedback-form" onSubmit={this.handleSubmit}>
                    <input id="csrf_token" type="hidden" name="csrf_token" value=""/>
                    <div class="form-row">
                        <div class="form-group col-lg-6 has-error has-feedback">
                            <input type="text" name="name" class="form-control" id="name" placeholder="Your Name" onChange={this.handleChange} />
                            <div class="validation">{this.state.errors.name}</div>
                        </div>
                        <div class="form-group col-lg-6">
                            <input type="email" class="form-control" name="email" id="email" placeholder="Your Email" onChange={this.handleChange} />
                            <div class="validation">{this.state.errors.email}</div>
                        </div>
                    </div>
                    <div class="form-group">
                        <input type="text" class="form-control" name="subject" id="subject" placeholder="Subject" onChange={this.handleChange} />
                        <div class="validation"></div>
                    </div>
                    <div class="form-group">
                        <textarea class="form-control" name="message" id="message" rows="5" placeholder="Message" onChange={this.handleChange}></textarea>
                        <div class="validation">{this.state.errors.message}</div>
                    </div>
                    <div class="text-center"><button type="submit" title="Send Message">Send Message</button></div>
                </form>
            </div>
        );
    }
}

ReactDOM.render(
    <FeedbackForm/>, document.getElementById("feedback-form")
);