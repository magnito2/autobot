class LogItem extends React.Component{
    render(){
        return (
            <tr>
                <td>{this.props.log.id}</td>
                <td>{this.props.log.thread_name}</td>
                <td>{this.props.log.level_name}</td>
                <td>{this.props.log.message}</td>
                <td>{formatTime(this.props.log.created_at)}</td>
            </tr>
        );
    }
}

function Paginate(props) {

    let pages = props.pages.map(page=>{
        return(<li className={page === props.current_page ? 'active' : '' }>
            <a href="#" onClick={page === props.current_page ? '' : props.get_logs_page.bind(this, page, props.search_value)}>{page}</a>
        </li>);
    });
    console.log(props.search_value);
    return (<ul class="pagination">
        {pages}
    </ul>);

}

class LogsTable extends React.Component{

    constructor(props){
        super(props);
        this.state = {
            data : null,
            pages : [],
            current_page: null,
            search_value: null
        };

        window.client = io.connect('//' + document.domain + ':' + location.port);
        const client =window.client;
        client.on('bot-log', (event)=> this.process_message(event));
        client.on('connect', function() {
            console.log("connected");
            client.emit("get-logs");
        });
        window.onbeforeunload = () => {
            ws.onclose = () => {};
            ws.close();
        }
    }

    process_message(event)
    {
        console.log("processing data");
        console.log(event);
        //let raw_data = JSON.parse(event);
        let raw_data = event['results'];
        if(raw_data){
            var new_data = this.state.data ? this.state.data.slice(0, 10): [];
            raw_data.map(data => {
                let d = {
                    'created_at' : parseDate(data.created_at),
                    'message' : data.msg,
                    'id' : data.id,
                    'thread_name' : data.threadName,
                    'level_name' : data.levelname
                };
                //console.log("Date ", data.close_time, parseDate(data.close_time))
                //return d;
                new_data.splice(0,0, d);
            });

            this.setState({data : new_data, pages: event['pages'], current_page: event['page'], search_value: event['search_word']});
            this.prop
        }

    }

    get_logs_page(page, search_word = undefined){
        console.log(`asking for page ${page} search for ${search_word}`);
        window.client.emit("get-logs", page, {"search_value" : search_word});
    }


    render(){

        if (this.state.data == null) {
            return <div>Loading...</div>
        }

        let logs = this.state.data.map(log => {
            return <LogItem log={log} key={parseInt(Math.random(9999999999) * Math.floor(999999999999))}/>
        });

        return (
            <div className="card">
                <div className="card-header" data-background-color="orange">
                    <h4 className="title">Logs</h4>
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
                <div class="card-footer">
                    <Paginate pages={this.state.pages} current_page={this.state.current_page} get_logs_page={this.get_logs_page}
                        search_value = {this.state.search_value}
                    />
                </div>
            </div>
        );
    }

}



const parseDate = d3.timeParse("%Q");
const formatTime = d3.timeFormat("%Y-%m-%d, %I:%M:%S");

ReactDOM.render(
    <LogsTable/>, document.getElementById("log-holder")
);