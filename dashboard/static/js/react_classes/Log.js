import React from "react";
import { render } from 'react-dom';
import {timeParse, timeFormat} from "d3-time-format";

class LogItem extends React.Component{
    render(){
        return (
            <tr>
                <td>{formatTime(this.props.time)}</td>
                <td>{this.props.activity}</td>
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
        const client = new WebSocket("ws://localhost:5678");
		client.onmessage = (event)=> this.process_message(event);
		client.onopen = (event)=> client.send(JSON.stringify({'action' : 'send_logs'}));
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
                                <th>Time</th>
                                <th>Activity</th>
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
        //console.log("processing data");
		let raw_data = JSON.parse(event.data);
		//console.log(raw_data['data']);

		if(raw_data['type'] === "logs"){
            var new_data = this.state.data ? this.state.data.slice(0, 20): [];
            raw_data['data'].map(data => {
                let d = {
                    'time' : parseDate(data.time),
                    'log' : data.log
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