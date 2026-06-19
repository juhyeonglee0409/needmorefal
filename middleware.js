export default function middleware(request) {
  const AUTH_USER = process.env.AUTH_USER || 'admin';
  const AUTH_PASS = process.env.AUTH_PASS || '';

  // 환경변수가 비어있으면 보호 비활성화 (로컬 개발용)
  if (!AUTH_PASS) {
    return;
  }

  const auth = request.headers.get('authorization');

  if (auth) {
    const [scheme, encoded] = auth.split(' ');
    if (scheme === 'Basic') {
      const decoded = atob(encoded);
      const [user, pass] = decoded.split(':');
      if (user === AUTH_USER && pass === AUTH_PASS) {
        return;
      }
    }
  }

  return new Response('Authentication required', {
    status: 401,
    headers: {
      'WWW-Authenticate': 'Basic realm="Protected"',
      'Content-Type': 'text/plain',
    },
  });
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
};
