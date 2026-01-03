const path = require("path");
const HtmlWebpackPlugin = require("html-webpack-plugin");
const CopyWebpackPlugin = require("copy-webpack-plugin");

module.exports = (env, options) => {
  const dev = options.mode === "development";
  const config = {
    devtool: dev ? "eval-source-map" : "source-map",
    entry: {
      taskpane: "./src/taskpane/taskpane.ts",
      commands: "./src/commands/commands.ts",
    },
    output: {
      path: path.resolve(__dirname, "dist"),
      filename: "[name].bundle.js",
      clean: true,
    },
    resolve: {
      extensions: [".ts", ".tsx", ".html", ".js"],
    },
    module: {
      rules: [
        {
          test: /\.ts$/,
          exclude: /node_modules/,
          use: {
            loader: "ts-loader",
          },
        },
        {
          test: /\.css$/,
          use: ["style-loader", "css-loader"],
        },
        {
          test: /\.(png|jpg|jpeg|gif|svg)$/,
          type: "asset/resource",
          generator: {
            filename: "assets/[name][ext]",
          },
        },
      ],
    },
    plugins: [
      new HtmlWebpackPlugin({
        filename: "taskpane.html",
        template: "./src/taskpane/taskpane.html",
        chunks: ["taskpane"],
      }),
      new HtmlWebpackPlugin({
        filename: "commands.html",
        template: "./src/taskpane/taskpane.html",
        chunks: ["commands"],
      }),
      new CopyWebpackPlugin({
        patterns: [
          {
            from: "manifest*.xml",
            to: "[name][ext]",
            transform(content) {
              if (dev) {
                return content.toString().replace(/https:\/\/localhost:3000/g, "https://localhost:3000");
              }
              return content;
            },
          },
          {
            from: "assets/*",
            to: "assets/[name][ext]",
          },
        ],
      }),
    ],
    devServer: {
      static: {
        directory: path.join(__dirname, "dist"),
      },
      headers: {
        "Access-Control-Allow-Origin": "*",
      },
      server: {
        type: "https",
      },
      port: 3000,
      hot: true,
      // Proxy API requests to backend (avoids mixed content HTTPS->HTTP)
      // Webpack dev server v5+ requires proxy to be an array
      proxy: [
        {
          context: ["/api", "/health"],
          target: "http://localhost:8000",
          changeOrigin: true,
          secure: false,
          logLevel: "debug",
        },
      ],
    },
  };

  return config;
};

