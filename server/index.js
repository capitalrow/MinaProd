import 'dotenv/config';
import express from 'express';
import http from 'http';
import path from 'path';
import { fileURLToPath } from 'url';
import cors from 'cors';
import attachTranscriptionSocket from './transcriptionSocket.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
app.use(cors());

// serve static files
app.use('/static', express.static(path.join(__dirname, '..', 'public', 'static')));
app.get('/live', (_, res) => {
  res.sendFile(path.join(__dirname, '..', 'public', 'templates', 'live.html'));
});
app.get('/', (_, res) => res.redirect('/live'));

const server = http.createServer(app);

// attach socket.io transcription namespace
attachTranscriptionSocket(server);

// start
const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
  console.log(`🚀 Mina server running on http://localhost:${PORT}`);
});