import React from "react";
import { render } from 'react-dom';
import {timeParse, timeFormat} from "d3-time-format";

class Kline extends React.Component {
        constructor(props)
        {
            super(props);
        }

        render(){
            return(
                <tr className={this.props.background}>
                    <td>${formatTime(this.props.data.close_time)}</td>
                    <td>${this.props.data.open}</td>
                    <td>${this.props.data.high}</td>
                    <td>${this.props.data.low}</td>
                    <td className="text-primary">${this.props.data.close}</td>
                </tr>
            );
        }
    }

    class KlinesTable extends React.Component {
        constructor(props){
            super(props);
        }

        render(){
            const klines_map = this.props.klines.map((data, index) => {
                let background_color;
                let next_kline = this.props.klines[index + 1];
                if (next_kline)
                {
                    if (data.close > next_kline.close)
                    {
                        background_color = " bg-success";
                    }
                    else if (data.close < next_kline.close)
                    {
                        background_color = " bg-danger";
                    }
                }

                return <Kline data={data} background={background_color} key={parseInt(Math.random(9999999999) * Math.floor(999999999999)).toString()}/>
            });
            return (
                <table className="table">
                    <thead className="text-primary">
                        <tr>
                            <th>Close Time</th>
                            <th>Open</th>
                            <th>High</th>
                            <th>Low</th>
                            <th>Close</th>
                        </tr>
                    </thead>
                    <tbody>
                        {klines_map}
                    </tbody>
                </table>
            );
        }
    }

    function Symbol(props){
        return (
            <div className="col-lg-3 col-md-6 col-sm-6">
                <div className="card card-stats">
                    <div className="card-header" data-background-color="green">
                        <i className="material-icons">store</i>
                    </div>
                    <div className="card-content">
                        <p className="category">Symbol</p>
                        <h3 className="title">{props.symbol}</h3>
                    </div>
                    <div className="card-footer">
                        <div className="stats">
                            <i className="material-icons">date_range</i> Last 24 Hours
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    function BrickSize(props)
    {
        return (
            <div className="col-lg-3 col-md-6 col-sm-6">
                <div className="card card-stats">
                    <div className="card-header" data-background-color="red">
                        <i className="material-icons">info_outline</i>
                    </div>
                    <div className="card-content">
                        <p className="category">Brick Size</p>
                        <h3 className="title">{props.brick_size}</h3>
                    </div>
                    <div className="card-footer">
                        <div className="stats">
                            <i className="material-icons">local_offer</i> last update: 1 day ago
                        </div>
                    </div>
                </div>
            </div>
        );
    }
    function TimeFrame(props)
    {
        return (
            <div className="col-lg-3 col-md-6 col-sm-6">
                <div className="card card-stats">
                    <div className="card-header" data-background-color="red">
                        <i className="material-icons">info_outline</i>
                    </div>
                    <div className="card-content">
                        <p className="category">Time Frame</p>
                        <h3 className="title">{props.time_frame}</h3>
                    </div>
                    <div className="card-footer">
                        <div className="stats">
                            <i className="material-icons">local_offer</i> last update: 1 day ago
                        </div>
                    </div>
                </div>
            </div>
        );
    }
    function Position(props)
    {
        return (
            <div className="col-lg-3 col-md-6 col-sm-6">
                <div className="card card-stats">
                    <div className="card-header" data-background-color="blue">
                        <i className="fa fa-twitter"></i>
                    </div>
                    <div className="card-content">
                        <p className="category">POSITION</p>
                        <h3 className="title">{props.position}</h3>
                    </div>
                    <div className="card-footer">
                        <div className="stats">
                            <i className="material-icons">update</i> Amount:
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    function LogsView(props) {
        return (
            <div>
                <div className="card-header" data-background-color="purple">
                    <h4 className="title">Logs</h4>
                    <p className="category">Logs from bot</p>
                </div>
                <div className="card-content table-responsive" id="log-table">

                </div>
            </div>
        );
    }

    function BotInformation(props)
    {
        return (
            <div>
                <Symbol symbol={props.info['pair']}/>
                <TimeFrame time_frame={props.info['time_frame']}/>
                <BrickSize brick_size={props.info['brick_size']}/>
                <Position position={props.info['position']}/>
            </div>
        );

    }

    function KlinesView(props) {
        return (
            <div>
                <div className="card-header" data-background-color="purple">
                <h4 className="title">Active Klines</h4>
                <p className="category">Klines from bot</p>
            </div>
            <div className="card-content table-responsive">
                <KlinesTable klines={props.klines}/>
            </div>
            </div>
        )
    }

    class IndexPage extends React.Component
    {
        constructor(props)
        {
            super(props);
            this.state = {
                'info' : {},
                'klines' : []
            };
            this.handleInputChange = this.handleInputChange.bind(this);
        }

        componentDidMount(){
            const ws = new WebSocket("ws://127.0.0.1:5678/");
            /**ws.onmessage = function (event) {
                var data = event.data;
                console.log(data)
                this.handleInputChange(data)
            };**/
            ws.onmessage = this.handleInputChange;
            ws.onopen = (event) => {
                ws.send(JSON.stringify({action : 'send_info'}));
                ws.send(JSON.stringify({action : 'send_klines'}))
            }
        }
        componentWillUnmount()
        {
            ws.close();
        }

        handleInputChange(event){
            //console.log(event);
            let data = JSON.parse(event.data);
            //console.log("data: ", data);

            if (data['type'] === "klines")
            {
                let klines = this.state.klines.slice(0,4);
                data['data'].map(
                    function (d) {
                        klines.splice(0,0,
                    {
                        open : parseFloat(d['open']).toPrecision(6),
                        high : parseFloat(d['high']).toPrecision(6),
                        low : parseFloat(d['low']).toPrecision(6),
                        close : parseFloat(d['close']).toPrecision(6),
                        close_time : parseDate(d['close_time'])
                    });
                    }
                );

                this.setState({
                    klines : klines,
                });
            }
            else if (data['type'] === "info")
            {
                this.setState({
                    info: data,
                })
            }
        }

        render()
        {
            return (
            <div>
                <div className="row">
                    <BotInformation info={this.state.info}/>
                </div>
                <div className="row">
                    <div className="col-lg-8 col-md-12">
                        <div className="card" id="klines">
                            <KlinesView klines={this.state.klines}/>
                        </div>
                    </div>
                    <div className="col-lg-4 col-md-12">
                        <div className="card" id="logs">
                            <LogsView/>
                        </div>
                    </div>
                </div>
            </div>
        );
        }
    }

render(<IndexPage/>, document.getElementById("index-page"));
const parseDate = timeParse("%Q");
const formatTime = timeFormat("%Y-%m-%d, %I:%M:%S");