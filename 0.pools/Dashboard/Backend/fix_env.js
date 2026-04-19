const fs = require('fs');
const path = require('path');
const envPath = path.join(__dirname, '.env');

try {
  let content = fs.readFileSync(envPath, 'utf8');
  // It literally starts with \n# Institutional... etc
  // We can just regex replace literal \n with real newline characters
  content = content.replace(/\\n/g, '\n');
  fs.writeFileSync(envPath, content, 'utf8');
  console.log("Fixed VPS .env newlines successfully.");
} catch (e) {
  console.error("Error fixing env:", e);
}
