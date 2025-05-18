
import os
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup

API_TOKEN = os.getenv("API_TOKEN")

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

class Form(StatesGroup):
    photo = State()
    name = State()
    address = State()
    phone1 = State()
    tech_id = State()
    problem_select = State()
    custom_problem = State()

def escape_md(text):
    return text.replace("-", "\-").replace(".", "\.").replace("(", "\(").replace(")", "\)").replace("`", "\`")

@dp.message_handler(commands='start')
@dp.message_handler(lambda message: message.text == "📋 ثبت گذارش جدید")
async def start_cmd(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("📷 گذشتن از این مرحله")
    await message.reply("👋!
در ابتدا لطف کنید و عکس از مشکل مشتری را بفرستید:", reply_markup=keyboard)
    await Form.photo.set()

@dp.message_handler(state=Form.photo, content_types=types.ContentTypes.ANY)
async def get_photo_or_skip(message: types.Message, state: FSMContext):
    if message.content_type == types.ContentType.PHOTO:
        await state.update_data(photo=message.photo[-1].file_id)
    elif message.text == "📷 گذشتن از این مرحله":
        await state.update_data(photo=None)
    else:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add("📷 گذشتن از این مرحله")
        await message.reply("لطفاً عکس بفرستید یا روی «📷 گذشتن از این مرحله» کلیک کنید.", reply_markup=keyboard)
        return

    await message.reply("👤 نام و تخلص مشتری را وارد کنید:", reply_markup=types.ReplyKeyboardRemove())
    await Form.name.set()

@dp.message_handler(state=Form.name)
async def get_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.reply("📍 آدرس مشتری را وارد کنید:")
    await Form.address.set()

@dp.message_handler(state=Form.address)
async def get_address(message: types.Message, state: FSMContext):
    await state.update_data(address=message.text)
    await message.reply("📞 لطفاً یک یا دو شماره تماس مشتری را وارد کنید:\nمثال:\n0729454545\n0798545454")
    await Form.phone1.set()

@dp.message_handler(state=Form.phone1)
async def get_phones(message: types.Message, state: FSMContext):
    numbers = message.text.strip().split('\n')
    phone1 = numbers[0] if len(numbers) > 0 else "❌"
    phone2 = numbers[1] if len(numbers) > 1 else "❌"
    await state.update_data(phone1=phone1, phone2=phone2)
    await message.reply("🧑‍🔧 آیدی تکنیسن را وارد کنید:")
    await Form.tech_id.set()

@dp.message_handler(state=Form.tech_id)
async def get_tech_id(message: types.Message, state: FSMContext):
    await state.update_data(tech_id=message.text)

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("مشکل قطع وصلی کیبل دارن")
    keyboard.add("ایتر 1 شان قطع نشان میده")
    keyboard.add("مشکل سیگنال دارین")
    keyboard.add("مشکل سی سی کیو دارن")
    keyboard.add("مشکل سیگنال و سی سی کیو دارن")
    keyboard.add("آفلاین استن")
    keyboard.add("✍️ مشکل را خودتان وارد کنید")

    await message.reply("⚠️ لطفاً یکی از مشکلات زیر را انتخاب کنید:", reply_markup=keyboard)
    await Form.problem_select.set()

@dp.message_handler(state=Form.problem_select)
async def select_problem(message: types.Message, state: FSMContext):
    if message.text == "✍️ مشکل را خودتان وارد کنید":
        await message.reply("لطفاً مشکل را بنویسید:", reply_markup=types.ReplyKeyboardRemove())
        await Form.custom_problem.set()
    else:
        await state.update_data(problem=message.text)
        await send_summary(message, state)

@dp.message_handler(state=Form.custom_problem)
async def get_custom_problem(message: types.Message, state: FSMContext):
    await state.update_data(problem=message.text)
    await send_summary(message, state)

async def send_summary(message: types.Message, state: FSMContext):
    data = await state.get_data()

    name = escape_md(data['name'])
    address = escape_md(data['address'])
    phone1 = escape_md(data.get('phone1', '❌'))
    phone2 = escape_md(data.get('phone2', '❌'))
    tech_id = escape_md(data['tech_id'])
    problem = escape_md(data['problem'])

    caption = (
        f"👤 نام کامل مشتری: {name}\n"
        f"📍 آدرس: {address}\n"
        f"📞 شماره تماس اول: `{phone1}`\n"
        f"📞 شماره تماس دوم: `{phone2}`\n"
        f"🧑‍🔧 آیدی تکنیسن: `{tech_id}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ {problem}"
    )

    if data.get('photo'):
        await bot.send_photo(chat_id=message.chat.id, photo=data['photo'], caption=caption, parse_mode="MarkdownV2")
    else:
        await bot.send_message(chat_id=message.chat.id, text=caption, parse_mode="MarkdownV2")

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("📋 ثبت گذارش جدید")
    await message.reply("✅ گذارش ثبت شد.", reply_markup=keyboard)
    await state.finish()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
