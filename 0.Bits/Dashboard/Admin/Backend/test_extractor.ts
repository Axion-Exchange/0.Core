function findEmail(obj: any): string | undefined {
  if (!obj || typeof obj !== 'object') return undefined;
  
  if (obj.email && typeof obj.email === 'string' && obj.email.includes('@')) return obj.email;
  if (obj.email_address && typeof obj.email_address === 'string' && obj.email_address.includes('@')) return obj.email_address;
  if (obj.email_address?.email && typeof obj.email_address.email === 'string') return obj.email_address.email;
  
  for (const key of Object.keys(obj)) {
    const found = findEmail(obj[key]);
    if (found) return found;
  }
  return undefined;
}
const payload = {
  data: {
    decision: {
      applicant: {
        contact: {
          email_address: "test@example.com"
        }
      }
    }
  }
};
console.log(findEmail(payload));
