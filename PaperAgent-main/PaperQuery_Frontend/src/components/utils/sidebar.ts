import { LayoutDashboard, LibraryBig, MessagesSquare, FlaskConical, UsersRound } from 'lucide-vue-next'

interface SidebarItem {
  title: string
  icon: any
  link: string
}

export const sidebarItems : SidebarItem[] = [
  {
    title: '概览',
    icon: LayoutDashboard,
    link: '/home/dashboard',
  },
  {
    title: '论文库',
    link: '/home/library',
    icon: LibraryBig,
  },
  {
    title: '智能问答',
    link: '/home/chat',
    icon: MessagesSquare,
  },
  {
    title: '深度研究',
    link: '/home/research',
    icon: FlaskConical,
  },
  // 论坛模块已隐藏 - 恢复时取消此注释即可
  // {
  //   title: '论坛',
  //   link: '/home/forum/threads',
  //   icon: UsersRound,
  // },
]
