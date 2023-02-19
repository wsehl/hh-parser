import urllib.request as r
import csv
from bs4 import BeautifulSoup

USD_KZT = 449.42
EUR_KZT = 482.01
RUB_KZT = 6.11


def parse_resume_page(url):
    html = r.urlopen(url)
    response = html.read().decode('utf8')
    soup = BeautifulSoup(response, 'html.parser')

    title = soup.find(
        'span', {'data-qa': 'resume-block-title-position'})

    if title is not None:
        title = title.text.strip()

    salary_string = soup.find(
        'span', {'data-qa': 'resume-block-salary'}
    )
    salary = None

    if salary_string is not None:
        salary_string = salary_string.text.strip()
        salary = ''.join(filter(str.isdigit, salary_string))

        if 'USD' in salary_string:
            salary = int(salary) * USD_KZT
        elif 'EUR' in salary_string:
            salary = int(salary) * EUR_KZT
        elif 'руб' in salary_string:
            salary = int(salary) * RUB_KZT

    specializations = soup.find_all(
        'li', {'data-qa': 'resume-block-position-specialization'}
    )

    if specializations is not None:
        specializations = [spec.text.strip() for spec in specializations]

    age = soup.find(
        'span', {'data-qa': 'resume-personal-age'}
    )

    if age is not None:
        age = age.text.strip()
        age = ''.join(filter(str.isdigit, age))

    employment_block = soup.find(
        'div', {'class': 'resume-block-container'}
    )

    employment_soup = BeautifulSoup(
        str(employment_block), 'html.parser')

    ps = employment_soup.find_all('p')

    employment = ps[0] if len(ps) > 0 else None
    work_schedule = ps[1] if len(ps) > 1 else None

    if employment is not None:
        # remove Занятость: from text
        employment = employment.text.strip()[11:]

    if work_schedule is not None:
        # remove График работы: from text
        work_schedule = work_schedule.text.strip()[15:]

    experience = soup.find(
        'span', {
            'class': 'resume-block__title-text resume-block__title-text_sub'}
    )

    experience_soup = BeautifulSoup(str(experience), 'html.parser')

    exp = experience_soup.find_all('span')

    experience_years = exp[1] if len(exp) > 1 else None
    experience_month = exp[2] if len(exp) > 2 else None

    if experience_years is not None:
        experience_years = experience_years.text.strip()
        experience_years = ''.join(filter(str.isdigit, experience_years))

    if experience_month is not None:
        experience_month = experience_month.text.strip()
        experience_month = ''.join(filter(str.isdigit, experience_month))

    additional_info = soup.find(
        'div', {
            'data-qa': 'resume-block-additional'}
    )

    additional_info_soup = BeautifulSoup(
        str(additional_info), 'html.parser')

    additional_info_container = additional_info_soup.find(
        'div', {'class': 'resume-block-item-gap'})

    additional_info_container_soup = BeautifulSoup(
        str(additional_info_container), 'html.parser')

    citizenship = additional_info_container_soup.find('p')

    if citizenship is not None:
        citizenship = citizenship.text.strip()
        # remove Гражданство: from text
        citizenship = citizenship[13:]

        if citizenship == 'Kazakhstan':
            citizenship = 'Казахстан'

        if citizenship == 'Uzbekistan':
            citizenship = 'Узбекистан'

        if citizenship == 'Russia':
            citizenship = 'Россия'

    sex = soup.find(
        'span', {'data-qa': 'resume-personal-gender'}
    )

    if sex is not None:
        sex = sex.text.strip()
        sex = True if sex == 'Мужчина' else False

    cv = (
        title,
        specializations,
        salary,
        age,
        employment,
        work_schedule,
        experience_years,
        experience_month,
        citizenship,
        sex
    )

    return cv


def create_file_name(search_text):
    return search_text.replace(' ', '_') + '_resumes' + '.csv'


def parse_resumes(search_text, max_resumes=500):
    page = 0
    resumes = []

    print(f'Starting to parse {max_resumes} {search_text} resumes...')

    while len(resumes) < max_resumes:
        url = f"https://hh.kz/search/resume?text={search_text}&page={page}&area=40&isDefaultArea=true&pos=full_text&logic=normal&exp_period=all_time&currency_code=KZT&ored_clusters=true&order_by=relevance"

        html = r.urlopen(url)
        response = html.read().decode('utf8')
        soup = BeautifulSoup(response, 'html.parser')

        cv_cards = soup.find_all('div', {'data-qa': 'resume-serp__resume'})

        max_possible_resumes_html = soup.find('div', {
            'data-qa': 'bloko-header-3'}
        )

        max_possible_resumes_text = max_possible_resumes_html.text.strip(
        ) if max_possible_resumes_html is not None else ''

        max_possible_resumes_text_number = max_possible_resumes_text[8:max_possible_resumes_text.find(
            "резюме")]

        max_possible_resumes = ''.join(
            filter(str.isdigit, max_possible_resumes_text_number))

        if max_resumes > int(max_possible_resumes):
            print(
                f'max_resumes is more than max_possible_resumes. Slicing it to {max_possible_resumes}')
            max_resumes = int(max_possible_resumes)

        if len(cv_cards) > max_resumes:
            print(
                f'Found more resumes than max_resumes, slicing it to {max_resumes}')
            cv_cards = cv_cards[:max_resumes]

        if len(cv_cards) == 0:
            print(f'No resumes found on page {page + 1}')
            break
        else:
            print(f'Found {len(cv_cards)} resumes on page {page + 1}')

        for cv_card in cv_cards:
            cv_url = cv_card.find(
                'a', {'data-qa': 'serp-item__title'})['href']

            # removing url params to get rid of highlighting
            clean_cv_url = "https://hh.kz" + cv_url.split('?')[0]

            resumes.append(parse_resume_page(clean_cv_url))
            print(f'Parsed {len(resumes)}/{max_resumes} resumes')

            if (len(resumes) == max_resumes):
                break

        page = page + 1

    print(f'Finished parsing {max_resumes} {search_text} resumes')
    print(f'Result: parsed {len(resumes)} resumes')

    file_name = create_file_name(search_text)

    with open(file_name, 'w', encoding='UTF8', newline='') as csv_file:
        fieldnames = ['Title', 'Specialization', 'Salary', 'Age', 'Employment',
                      'Work schedule', 'Experience years', 'Experience month', 'Citizenship', 'Sex']
        writer = csv.writer(csv_file)
        writer.writerow(fieldnames)

        for resume in resumes:
            writer.writerow(resume)

    return file_name
