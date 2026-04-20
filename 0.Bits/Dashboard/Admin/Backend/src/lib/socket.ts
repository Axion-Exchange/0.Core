import { Server as SocketIOServer } from 'socket.io';
import { Server as HttpServer } from 'http';
import { createLogger } from './logger.js';
import { config } from '../config/index.js';

const log = createLogger('socket.io');

let io: SocketIOServer | null = null;

export const initSocket = (server: HttpServer) => {
  io = new SocketIOServer(server, {
    cors: {
      origin: config.CORS_ORIGINS ? config.CORS_ORIGINS.split(',') : '*',
      methods: ['GET', 'POST']
    }
  });

  io.on('connection', (socket) => {
    log.info(`Client connected to WebSockets [${socket.id}]`);
    
    socket.on('disconnect', () => {
      log.info(`Client disconnected [${socket.id}]`);
    });
  });

  log.info('WebSocket bridge initialized.');
  return io;
};

export const getSocket = (): SocketIOServer => {
  if (!io) {
    throw new Error('Socket.io must be initialized before fetching it.');
  }
  return io;
};
