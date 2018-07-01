const webpack = require('webpack');

const config = {
    entry:  {
        'index' : __dirname + '/js/index.jsx',
        'logs' : __dirname + '/js/react_classes/Log.js',
        'dashboard' : __dirname + '/js/react_classes/DashBoard.js'
    },
    output: {
        path: __dirname + '/dist',
    },
    resolve: {
        extensions: ['.js', '.jsx', '.css']
    },
    module: {
        rules: [
            {
                test: /\.jsx?/,
                exclude: /node_modules/,
                use: 'babel-loader'
            }
        ]
    },
};

module.exports = config;