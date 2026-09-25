import { PlayCircle, ListMusic, User, FlaskConical } from 'lucide-vue-next'

interface SidebarItem {
  title: string
  icon: any
  link: string
}

export const sidebarItems : SidebarItem[] = [
  {
    title: 'DashBoard',
    icon: PlayCircle,
    link: '/home/dashboard',
  },
  {
    title: 'Library',
    link: '/home/library',
    icon: ListMusic,
  },
  {
    title: 'Chat',
    link: '/home/chat',
    icon: User,
  },
  {
    title: 'Research',
    link: '/home/research',
    icon: FlaskConical,
  },
  {
    title: '论坛',
    link: '/home/forum/threads',
    icon: User,
  },
]
