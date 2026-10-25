// 登录 API：提供用户昵称登录与管理员账号登录的 mock 实现。
const ADMIN_USERNAME = 'admin'
// TODO: 接入后端后删除写死的管理员凭据。
const ADMIN_PASSWORD = 'admin123'

function sleep(ms) {
  return new Promise((resolve) => {
    setTimeout(resolve, ms)
  })
}

function random(min, max) {
  return Math.round(Math.random() * (max - min) + min)
}

export async function login(nickname) {
  await sleep(random(400, 800))

  const normalizedNickname = nickname.trim()

  if (normalizedNickname.length < 2) {
    throw new Error('昵称至少需要 2 个字')
  }

  return {
    role: 'user',
    nickname: normalizedNickname,
  }
}

export async function adminLogin(username, password) {
  await sleep(random(400, 800))

  if (username !== ADMIN_USERNAME || password !== ADMIN_PASSWORD) {
    throw new Error('账号或密码错误')
  }

  return {
    role: 'admin',
    nickname: username,
  }
}
