'use strict';

var _createClass = function () { function defineProperties(target, props) { for (var i = 0; i < props.length; i++) { var descriptor = props[i]; descriptor.enumerable = descriptor.enumerable || false; descriptor.configurable = true; if ("value" in descriptor) descriptor.writable = true; Object.defineProperty(target, descriptor.key, descriptor); } } return function (Constructor, protoProps, staticProps) { if (protoProps) defineProperties(Constructor.prototype, protoProps); if (staticProps) defineProperties(Constructor, staticProps); return Constructor; }; }();

function _classCallCheck(instance, Constructor) { if (!(instance instanceof Constructor)) { throw new TypeError("Cannot call a class as a function"); } }

function _possibleConstructorReturn(self, call) { if (!self) { throw new ReferenceError("this hasn't been initialised - super() hasn't been called"); } return call && (typeof call === "object" || typeof call === "function") ? call : self; }

function _inherits(subClass, superClass) { if (typeof superClass !== "function" && superClass !== null) { throw new TypeError("Super expression must either be null or a function, not " + typeof superClass); } subClass.prototype = Object.create(superClass && superClass.prototype, { constructor: { value: subClass, enumerable: false, writable: true, configurable: true } }); if (superClass) Object.setPrototypeOf ? Object.setPrototypeOf(subClass, superClass) : subClass.__proto__ = superClass; }

var LogItem = function (_React$Component) {
    _inherits(LogItem, _React$Component);

    function LogItem() {
        _classCallCheck(this, LogItem);

        return _possibleConstructorReturn(this, (LogItem.__proto__ || Object.getPrototypeOf(LogItem)).apply(this, arguments));
    }

    _createClass(LogItem, [{
        key: 'render',
        value: function render() {
            return React.createElement(
                'tr',
                null,
                React.createElement(
                    'td',
                    null,
                    this.props.log.id
                ),
                React.createElement(
                    'td',
                    null,
                    this.props.log.thread_name
                ),
                React.createElement(
                    'td',
                    null,
                    this.props.log.level_name
                ),
                React.createElement(
                    'td',
                    null,
                    this.props.log.message
                ),
                React.createElement(
                    'td',
                    null,
                    formatTime(this.props.log.created_at)
                )
            );
        }
    }]);

    return LogItem;
}(React.Component);

function Paginate(props) {
    var _this2 = this;

    var pages = props.pages.map(function (page) {
        return React.createElement(
            'li',
            { className: page === props.current_page ? 'active' : '' },
            React.createElement(
                'a',
                { href: '#', onClick: page === props.current_page ? '' : props.get_logs_page.bind(_this2, page, props.search_value) },
                page
            )
        );
    });
    console.log(props.search_value);
    return React.createElement(
        'ul',
        { 'class': 'pagination' },
        pages
    );
}

var LogsTable = function (_React$Component2) {
    _inherits(LogsTable, _React$Component2);

    function LogsTable(props) {
        _classCallCheck(this, LogsTable);

        var _this3 = _possibleConstructorReturn(this, (LogsTable.__proto__ || Object.getPrototypeOf(LogsTable)).call(this, props));

        _this3.state = {
            data: null,
            pages: [],
            current_page: null,
            search_value: null
        };

        window.client = io.connect('http://' + document.domain + ':' + location.port);
        var client = window.client;
        client.on('bot-log', function (event) {
            return _this3.process_message(event);
        });
        client.on('connect', function () {
            console.log("connected");
            client.emit("get-logs");
        });
        window.onbeforeunload = function () {
            ws.onclose = function () {};
            ws.close();
        };
        return _this3;
    }

    _createClass(LogsTable, [{
        key: 'process_message',
        value: function process_message(event) {
            console.log("processing data");
            console.log(event);
            //let raw_data = JSON.parse(event);
            var raw_data = event['results'];
            if (raw_data) {
                var new_data = this.state.data ? this.state.data.slice(0, 10) : [];
                raw_data.map(function (data) {
                    var d = {
                        'created_at': parseDate(data.created_at),
                        'message': data.msg,
                        'id': data.id,
                        'thread_name': data.threadName,
                        'level_name': data.levelname
                    };
                    //console.log("Date ", data.close_time, parseDate(data.close_time))
                    //return d;
                    new_data.splice(0, 0, d);
                });

                this.setState({ data: new_data, pages: event['pages'], current_page: event['page'], search_value: event['search_word'] });
                this.prop;
            }
        }
    }, {
        key: 'get_logs_page',
        value: function get_logs_page(page) {
            var search_word = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : undefined;

            console.log('asking for page ' + page + ' search for ' + search_word);
            window.client.emit("get-logs", page, { "search_value": search_word });
        }
    }, {
        key: 'render',
        value: function render() {

            if (this.state.data == null) {
                return React.createElement(
                    'div',
                    null,
                    'Loading...'
                );
            }

            var logs = this.state.data.map(function (log) {
                return React.createElement(LogItem, { log: log, key: parseInt(Math.random(9999999999) * Math.floor(999999999999)) });
            });

            return React.createElement(
                'div',
                { className: 'card' },
                React.createElement(
                    'div',
                    { className: 'card-header', 'data-background-color': 'orange' },
                    React.createElement(
                        'h4',
                        { className: 'title' },
                        'Logs'
                    ),
                    React.createElement(
                        'p',
                        { className: 'category' },
                        'Logs from latest ',
                        logs.length
                    )
                ),
                React.createElement(
                    'div',
                    { className: 'card-content table-responsive' },
                    React.createElement(
                        'table',
                        { className: 'table' },
                        React.createElement(
                            'thead',
                            { className: 'text-primary' },
                            React.createElement(
                                'tr',
                                null,
                                React.createElement(
                                    'th',
                                    null,
                                    'ID'
                                ),
                                React.createElement(
                                    'th',
                                    null,
                                    'ThreadName'
                                ),
                                React.createElement(
                                    'th',
                                    null,
                                    'Level Name'
                                ),
                                React.createElement(
                                    'th',
                                    null,
                                    'Message'
                                ),
                                React.createElement(
                                    'th',
                                    null,
                                    'Created At'
                                )
                            )
                        ),
                        React.createElement(
                            'tbody',
                            null,
                            logs
                        )
                    )
                ),
                React.createElement(
                    'div',
                    { 'class': 'card-footer' },
                    React.createElement(Paginate, { pages: this.state.pages, current_page: this.state.current_page, get_logs_page: this.get_logs_page,
                        search_value: this.state.search_value
                    })
                )
            );
        }
    }]);

    return LogsTable;
}(React.Component);

var parseDate = d3.timeParse("%Q");
var formatTime = d3.timeFormat("%Y-%m-%d, %I:%M:%S");

ReactDOM.render(React.createElement(LogsTable, null), document.getElementById("log-holder"));