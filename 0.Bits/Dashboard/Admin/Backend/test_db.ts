import { prisma } from './src/lib/db.js';
const res = await prisma.systemSetting.findUnique({ where: { key: 'MEXC_SPOT_USDTMXN_MID' } });
console.log(res);
