/**
 * babyCourses.js — static catalog of the baby-prep courses archived to Google
 * Drive (Brunna's Hotmart purchases, saved before access expired).
 *
 * Consumed by CursosView.jsx and rendered as an embedded Drive player/PDF
 * viewer. Each lesson carries a Google Drive file id; playback uses the Drive
 * preview embed (https://drive.google.com/file/d/<driveId>/preview), which
 * relies on the parent folder's "anyone with the link" sharing.
 *
 * Shape:
 *   course  = { id, title, subtitle?, modules: [module] }
 *   module  = { title, lessons: [lesson] }
 *   lesson  = { title, type: 'video' | 'pdf', driveId, duration? }
 *
 * To add content later: drop a new entry here — no backend, no rebuild of any
 * data pipeline. driveId is the id from the file's Drive share link.
 */

export const BABY_COURSES = [
  {
    id: 'maternidade',
    title: '5 Aulas para a Maternidade',
    subtitle: 'Preparo emocional e prático para a chegada do bebê',
    modules: [
      {
        title: 'Aulas',
        lessons: [
          { title: 'Boas-vindas', type: 'video', driveId: '1Y51G8Xw17vtuChIMRUcK3xdZVEzEc2l0' },
          { title: 'Autocuidado', type: 'video', driveId: '1IO6IB8ji4At3meCJ0Q9rfLbJ2h1WQBNw' },
          { title: 'Organização', type: 'video', driveId: '1tNfE0BRWcOYjnoDCsHQuE9dz0Bd0671R' },
          { title: 'Você vai dormir?', type: 'video', driveId: '1dKNEpxJZvIDFqR4Hj_z7N-VI4ojoL3Ds' },
          { title: 'Relacionamento', type: 'video', driveId: '1IU-K1PwKFLzoqX35BgA06AZqqlF42bo_' },
          { title: 'Mudanças', type: 'video', driveId: '16COUshNtYzTI29Nn4S3PXXOklLV8yUUD' },
          { title: 'Ponto final', type: 'video', driveId: '19jxu84l3wFXInjWFg_9XN5nnCwWcGVHr' },
        ],
      },
    ],
  },
  {
    id: 'enxoval',
    title: 'Enxoval Inteligente',
    subtitle: '8 módulos + aulas bônus + oficina de carrinhos',
    modules: [
      {
        title: '1 · Planilha Inteligente',
        lessons: [
          { title: 'Planilha Inteligente', type: 'video', driveId: '1iZSOUYzJ6cwKH97AAr5NgwzYijbJaXC5' },
          { title: 'Planner da Gestante', type: 'video', driveId: '1owSAoPUWnt_ISEfSw6oA8bob3NnouTx9' },
          { title: 'E-book completo do curso', type: 'pdf', driveId: '1DS5cUVB4d7Ie5zZo2rc9WTAXOHqQupHK' },
        ],
      },
      {
        title: '2 · Quarto do Bebê',
        lessons: [
          { title: 'Babá eletrônica', type: 'video', driveId: '14eDVKPb-GB5Zi8_Wcb4SRIKYOpGZL_s5' },
          { title: 'Cômoda ou guarda-roupa', type: 'video', driveId: '1FMJPQur786UWbeKSE1_g7SS1TQQkb8rY' },
          { title: 'Poltrona de amamentação', type: 'video', driveId: '1W4a--dDiuQE-9RcbG0HaG3g8DpXLiDRU' },
          { title: 'Trocador eficiente', type: 'video', driveId: '1RM5NqvSdXjpUwTOWxSKdQE4dU1b1n4Td' },
        ],
      },
      {
        title: '3 · Como Vestir o Bebê',
        lessons: [
          { title: 'Tipos de roupas', type: 'video', driveId: '1hrR_6r27Zdp9tKQijrfzJ3ewpFqo-IN6' },
          { title: 'Como vestir o bebê', type: 'video', driveId: '1wnEDlg_cLn3oV1BZy4RpDLyEGDN9Z2zg' },
          { title: 'Cueiros, mantas e fraldas', type: 'video', driveId: '1lExB1lbikCidxYeEQWYFMUk-FwmOUr7c' },
          { title: 'Guia de marcas e tamanhos', type: 'video', driveId: '1lbzqJZZcPXfnP1wgOcSU6-VKst3PUSzq' },
          { title: 'Roupas para o calor', type: 'video', driveId: '1oaC2PIwOvrrHZsVJfP0WE0cDakvLVMRn' },
          { title: 'Roupas para o frio', type: 'video', driveId: '1TggD25WKzzzqDxKOUC0oekJ_ZqN_8qGZ' },
          { title: 'Rotina: suja, suja, lava', type: 'video', driveId: '1O1Zwp4GJhbpR8xhS_Mb2iXee-GqPKvni' },
        ],
      },
      {
        title: '4 · Carrinho e Rotina',
        lessons: [
          { title: 'Escolha o melhor carrinho', type: 'video', driveId: '11F2CEvXONx1mHSrJeAaLC6wZFvc0WpTE' },
          { title: 'Bebê conforto ou cadeirinha', type: 'video', driveId: '1Czk9Kp1A6LwPgNLyU1at5Ub3p61s7UKF' },
          { title: 'Aula prática: cadeirinhas', type: 'video', driveId: '1QKJTQJhsbXW20qFP_lfYd3DIByXBUFSx' },
          { title: 'Economizar R$750 nos carrinhos (Amazon)', type: 'video', driveId: '1uxPA2bNu7riYIWEL64kn1TOKwgyUiY6G' },
          { title: 'Sling ou canguru', type: 'video', driveId: '1mlffAdpK12OXMGt_NmjhmMsssHzzEqLa' },
          { title: 'Ninho, cadeirinha e swaddle', type: 'video', driveId: '1ymnwQf329hVTWnorttSFswLQlNcDlu2W' },
          { title: 'Mochila de passeio', type: 'video', driveId: '1rhPKX4fWHtmA7qIVIRhoSDK8nTVFteyA' },
          { title: 'Brinquedos', type: 'video', driveId: '1ZjwQsi3_d0QaQ_J0FLlFW66Hoi4EEsDZ' },
          { title: 'Itens de introdução alimentar', type: 'video', driveId: '13ci48oBW-c-iIa7_6P77kQmIEvcuCZH7' },
        ],
      },
      {
        title: '5 · Higiene e Fraldas',
        lessons: [
          { title: 'Produtos de higiene', type: 'video', driveId: '1CXoVN2cOVeZh1WCt45FmToqvulji3GQo' },
          { title: 'Banheira', type: 'video', driveId: '1a8bd8YPtLsBXae8WuPVsWx3KzK-8cH5b' },
          { title: 'Fraldas descartáveis + lista de chá', type: 'video', driveId: '1ovMJ1N7pDjcCPG5Sv1QIA7J3eubrxts8' },
          { title: 'Fraldas ecológicas', type: 'video', driveId: '1L_GNYDJebYeODioJntOQDZUQ_P7NBivc' },
        ],
      },
      {
        title: '6 · Lavar e Organizar',
        lessons: [
          { title: 'Como lavar as roupinhas', type: 'video', driveId: '1awW9UG6CodiyHj3cs6I3KyT0ddfN2zUx' },
          { title: 'Colmeias e organizadores', type: 'video', driveId: '1fSxawYdD8N0B75iNzrrGf7Jl2rj13IF6' },
          { title: 'Dobre em 1, 2, 3', type: 'video', driveId: '1lHR310mBW-0YYvV49VSCCb8_353QTABs' },
        ],
      },
      {
        title: '7 · Acessórios de Amamentação',
        lessons: [
          { title: 'Acessórios de amamentação', type: 'video', driveId: '1--pACmgwjJWmGCQvlVliuT79nSJrqqxM' },
          { title: 'Extratoras de leite', type: 'video', driveId: '1E51X8UeTJyRihXFnIdVhEMbCvvVyX_EJ' },
          { title: 'Sutiãs e roupas de amamentação', type: 'video', driveId: '17SKmSBzoZYs4KULEeEIrrQhUkuSh5HS5' },
          { title: 'Opcionais: chupeta e mamadeira', type: 'video', driveId: '1R8q0ALVLYdfmS9RnjNUvYLdKFYcoE64H' },
        ],
      },
      {
        title: '8 · Mala Maternidade',
        lessons: [
          { title: 'Mala do bebê', type: 'video', driveId: '1hS4F-4-qagr2pW9sOm0xJU_0mnhgj80L' },
          { title: 'Mala da mãe', type: 'video', driveId: '13Em7lnHzMqHRWM8eXUsXjIXQ-0Ot6LU2' },
          { title: 'Último check antes do parto', type: 'video', driveId: '1Sdw8G9ffO7oJtIkYA_34FoONXXOtMEQM' },
        ],
      },
      {
        title: 'Aulas Bônus',
        lessons: [
          { title: 'Oficina de Roupinhas', type: 'video', driveId: '1Qo_vBOZFg3GbfGnytiIqSZ4eV_-nCNft', duration: '1:12:19' },
          { title: 'E se o bebê não passar no Teste da Linguinha?', type: 'video', driveId: '1NmlwZlxa7TMTt2XzSUQG5A_G_Xj_nSDp', duration: '7:33' },
          { title: 'Fotos essenciais para tirar do bebê', type: 'video', driveId: '1ypHaQObvYMGwzsZg0chJvKxEG2TXYreN', duration: '57:11' },
          { title: 'Sono do recém-nascido', type: 'video', driveId: '1sf8NcRgp4gJQHphsmkqMKaUnOsVkJCPh', duration: '44:18' },
          { title: 'Oficina de Introdução Alimentar', type: 'video', driveId: '1z4IUSbX4fIy64sHnvDs7b_VhB_nZjaIj', duration: '1:23:45' },
        ],
      },
      {
        title: 'Oficina de Carrinhos',
        lessons: [
          { title: 'Oficina de Carrinhos (17/03)', type: 'video', driveId: '1lqGOjQUvOYqF_5gijg5i2XhKV26wEIdV', duration: '1:24:02' },
        ],
      },
    ],
  },
  {
    id: 'ano-de-ouro',
    title: 'E-book · O Ano de Ouro',
    subtitle: 'Guia do primeiro ano do bebê (305 páginas)',
    modules: [
      {
        title: 'E-book',
        lessons: [
          { title: 'O Ano de Ouro — primeiro ano do bebê', type: 'pdf', driveId: '1Ht6QmNbVE6_cFuRETkaqFdtfnJSBP6dG' },
        ],
      },
    ],
  },
]
