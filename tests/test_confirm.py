import pytest


def test_confirmation(loaded_pa):
    from pypa.confirmation import process_booking, \
        ReportParameters, ArgsWrapper
    import filecmp
    from os.path import join

    bk_no = 31132
    action = 'file'

    rp = ReportParameters(loaded_pa.env)
    rp.read_images()

    additional_text = ''
    forced_subject = ''

    args = ArgsWrapper({})

    files = process_booking(
        bk_no, args, loaded_pa, action, rp, additional_text, forced_subject)

    folder = loaded_pa.env.confirmations_folder

    verified_html_file_name = join(folder,  f'verified_{bk_no}.html')
    verified_text_file_name = join(folder, f'verified_{bk_no}.txt')

    generated_html_file_name = join(folder, files[0])
    generated_text_file_name = join(folder, files[1])
    assert(filecmp.cmp(generated_html_file_name, verified_html_file_name))
    assert(filecmp.cmp(generated_text_file_name, verified_text_file_name))

    # sql = (
    #     f"select * from pa..tblhistory where hist_bk_no={bk_no}"
    #     f" and convert(varchar(1000), hist_msg)='{files[0]}'")

    # res = loaded_pa.env.check_exists(sql)
    # if not res:
    #     loaded_pa.env.get_connection().commit()
    #     assert(False)
