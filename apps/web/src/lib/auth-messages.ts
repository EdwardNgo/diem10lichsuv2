export const authErrorMessages: Record<string, string> = {
  account_conflict:
    "Email này đã được gắn với một hồ sơ khác. Hãy dùng đúng tài khoản Google đã đăng nhập trước đó.",
  invalid_profile:
    "Tài khoản Google chưa có email đã xác minh. Hãy kiểm tra tài khoản hoặc dùng tài khoản khác.",
  invalid_state: "Phiên đăng nhập đã hết hạn. Hãy bấm đăng nhập lại.",
  missing_code: "Google chưa trả đủ thông tin đăng nhập. Hãy thử lại.",
  provider_error:
    "Không kết nối được Google. Hãy kiểm tra mạng rồi thử lại sau ít phút.",
};

export function authErrorMessage(code: string | null | undefined): string | null {
  if (code === null || code === undefined || code === "" || code === "cancelled") {
    return null;
  }
  return (
    authErrorMessages[code] ??
    "Không thể kết nối Google. Hãy kiểm tra mạng rồi thử lại."
  );
}
