import type { ReactNode } from "react";

import { AdminRequired } from "@/components/admin-required";

export default function AdminLayout({ children }: { children: ReactNode }) {
  return <AdminRequired>{children}</AdminRequired>;
}
