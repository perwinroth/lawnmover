const express = require('express');
const path = require('path');
const compression = require('compression');

const app = express();
const ROOT = __dirname; // serve whole friluft folder

app.use(compression());

// Basic headers for local dev
app.use((req, res, next) => {
  res.setHeader('X-Powered-By', 'friluft');
  next();
});

// Serve the entire folder so /web and /data are available
app.use(express.static(ROOT, { extensions: ['html'] }));

// Convenience redirect to the map
app.get('/', (req, res) => {
  res.redirect('/web/');
});

const port = process.env.PORT || 3000;
const host = process.env.HOST || '127.0.0.1';
app.listen(port, host, () => {
  console.log(`Friluft server running at http://${host}:${port}/web/`);
});

