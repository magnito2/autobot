import React from "react";
import { render } from 'react-dom';
import {timeParse, timeFormat} from "d3-time-format";

class LogItem extends React.Component{
    render(){
        return (
            <tr>
                <td>{this.props.id}</td>
                <td>{this.props.thread_name}</td>
                <td>{this.props.level_name}</td>
                <td>{this.props.message}</td>
                <td>{formatTime(this.props.created_at)}</td>
            </tr>
        );
    }
}

class LogsTable extends React.Component{

    constructor(props){
        super(props);
        this.state = {
            data : null
        };
        const client = io.connect('http://' + document.domain + ':' + location.port);
		client.on('bot-log', (event)=> this.process_message(event));
        client.on('connect', function() {
            console.log("connected");
        });
		window.onbeforeunload = () => {
		    ws.onclose = () => {};
		    ws.close();
        }
    }
    render(){

        if (this.state.data == null) {
			return <div>Loading...</div>
		}

        let logs = this.state.data.map(log => {
            return <LogItem time={log.time} activity={log.log} key={parseInt(Math.random(9999999999) * Math.floor(999999999999))}/>
        });

        return (
            <div className="card">
                <div className="card-header" data-background-color="purple">
                    <h4 className="title">Application Logs</h4>
                    <p className="category">Logs from latest {logs.length}</p>
                </div>
                <div className="card-content table-responsive">
                    <table className="table">
                        <thead className="text-primary">
                            <tr>
                                <th>ID</th>
                                <th>ThreadName</th>
                                <th>Level Name</th>
                                <th>Message</th>
                                <th>Created At</th>
                            </tr>
                        </thead>
                        <tbody>
                            {logs}
                        </tbody>
                    </table>
                </div>
            </div>
        );
    }

    process_message(event)
    {
        console.log("processing data");
		let raw_data = JSON.parse(event.data);
		console.log(raw_data['data']);

		if(raw_data['type'] === "logs"){
            var new_data = this.state.data ? this.state.data.slice(0, 20): [];
            raw_data['data'].map(data => {
                let d = {
                    'created_at' : parseDate(data.time),
                    'message' : data.msg,
                    'id' : data.id,
                    'thread_name' : data.thread_name,
                    'level_name' : data.level_name
                };
                //console.log("Date ", data.close_time, parseDate(data.close_time))
                //return d;
                new_data.splice(0,0, d);
            });
            //console.log("compare ",new_data);

            this.setState({data : new_data});
        }

    }

}

const parseDate = timeParse("%Q");
const formatTime = timeFormat("%Y-%m-%d, %I:%M:%S");

render(
    <LogsTable/>, document.getElementById("log-holder")
);