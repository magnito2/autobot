
import React from 'react';
import { render } from 'react-dom';
import Chart from './react_classes/Chart';
import { getData } from "./react_classes/utils"

import { TypeChooser } from "react-stockcharts/lib/helper";

import {timeParse} from "d3-time-format"


class ChartComponent extends React.Component {

	constructor(props)
	{
		super(props);
		const client = new WebSocket("ws://localhost:5678");
		client.onmessage = (event)=> this.process_message(event);
		client.onopen = (event)=> client.send(JSON.stringify({'action' : 'send_historical_klines'}));
	}

	componentDidMount() {
		getData().then(data => {
			console.log(data.data);
			this.setState({ data })
		});
	}
	render() {
		if (this.state == null) {
			return <div>Loading...</div>
		}
		return (
			<TypeChooser>
				{type => <Chart type={type} data={this.state.data} />}
			</TypeChooser>
		)
	}

	process_message(event)
	{
		console.log("processing data");
		let raw_data = JSON.parse(event.data);
        var new_data = this.state ? this.state.data.slice(0, 1500): [];
		let data = raw_data['data'].map(data => {
            let d = {
                'date' : parseDate(data.close_time),
                'open' : data.open,
                'close' : data.close,
                'high' : data.high,
                'low' : data.low,
				'volume' : data.volume
            }
            //console.log("Date ", data.close_time, parseDate(data.close_time))
            return d;
		});
		console.log("new klines are here", data);
		//new_data.push(data);
		console.log("new data", new_data);
		//console.log("state data" ,this.state.data);
		this.setState({data});

	}
}

render(
	<ChartComponent />,
	document.getElementById("content")
);

const parseDate = timeParse("%Q");