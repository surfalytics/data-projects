import base64
import unittest

import app.etl


class StructureTestSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.MODULE = app.etl
    
    def test_function_exists_calculate_experiment_final_scores(self):
        functions = _get_function_names(self.MODULE)
        self.assertIn(
            base64.b64decode(b'Y2FsY3VsYXRlX2V4cGVyaW1lbnRfZmluYWxfc2NvcmVz').decode(),
            functions,
            msg=f"The function "
                f"`{base64.b64decode(b'Y2FsY3VsYXRlX2V4cGVyaW1lbnRfZmluYWxfc2NvcmVz').decode()}` "
                f"is not found, but it was marked as required."
        )
        
    def test_function_signature_match_calculate_experiment_final_scores(self):
        functions = _get_function_names(self.MODULE)
        self.assertIn(
            base64.b64decode(b'Y2FsY3VsYXRlX2V4cGVyaW1lbnRfZmluYWxfc2NvcmVz').decode(),
            functions,
            msg=f"The function "
                f"`{base64.b64decode(b'Y2FsY3VsYXRlX2V4cGVyaW1lbnRfZmluYWxfc2NvcmVz').decode()}` "
                f"is not found, but it was marked as required."
        )
        args = _get_function_arg_names(
            self.MODULE,
            base64.b64decode(b'Y2FsY3VsYXRlX2V4cGVyaW1lbnRfZmluYWxfc2NvcmVz').decode()
        )
        self.assertEqual(
            1,
            len(args),
            msg=f"The function "
                f"`{base64.b64decode(b'Y2FsY3VsYXRlX2V4cGVyaW1lbnRfZmluYWxfc2NvcmVz').decode()}` "
                f"should have exactly 1 argument(s)."
        )
        args = _get_function_arg_names(
            self.MODULE,
            base64.b64decode(b'Y2FsY3VsYXRlX2V4cGVyaW1lbnRfZmluYWxfc2NvcmVz').decode()
        )
        self.assertEqual(
            base64.b64decode(b'ZGF0YQ==').decode(),
            args[0],
            msg=f"The argument #0 of function "
                f"`{base64.b64decode(b'Y2FsY3VsYXRlX2V4cGVyaW1lbnRfZmluYWxfc2NvcmVz').decode()}` "
                f"should be called "
                f"`data`."
        )
        
    def test_function_exists_filter_late_logs(self):
        functions = _get_function_names(self.MODULE)
        self.assertIn(
            base64.b64decode(b'ZmlsdGVyX2xhdGVfbG9ncw==').decode(),
            functions,
            msg=f"The function "
                f"`{base64.b64decode(b'ZmlsdGVyX2xhdGVfbG9ncw==').decode()}` "
                f"is not found, but it was marked as required."
        )
        
    def test_function_signature_match_filter_late_logs(self):
        functions = _get_function_names(self.MODULE)
        self.assertIn(
            base64.b64decode(b'ZmlsdGVyX2xhdGVfbG9ncw==').decode(),
            functions,
            msg=f"The function "
                f"`{base64.b64decode(b'ZmlsdGVyX2xhdGVfbG9ncw==').decode()}` "
                f"is not found, but it was marked as required."
        )
        args = _get_function_arg_names(
            self.MODULE,
            base64.b64decode(b'ZmlsdGVyX2xhdGVfbG9ncw==').decode()
        )
        self.assertEqual(
            2,
            len(args),
            msg=f"The function "
                f"`{base64.b64decode(b'ZmlsdGVyX2xhdGVfbG9ncw==').decode()}` "
                f"should have exactly 2 argument(s)."
        )
        args = _get_function_arg_names(
            self.MODULE,
            base64.b64decode(b'ZmlsdGVyX2xhdGVfbG9ncw==').decode()
        )
        self.assertEqual(
            base64.b64decode(b'ZGF0YQ==').decode(),
            args[0],
            msg=f"The argument #0 of function "
                f"`{base64.b64decode(b'ZmlsdGVyX2xhdGVfbG9ncw==').decode()}` "
                f"should be called "
                f"`data`."
        )
        args = _get_function_arg_names(
            self.MODULE,
            base64.b64decode(b'ZmlsdGVyX2xhdGVfbG9ncw==').decode()
        )
        self.assertEqual(
            base64.b64decode(b'aG91cnM=').decode(),
            args[1],
            msg=f"The argument #1 of function "
                f"`{base64.b64decode(b'ZmlsdGVyX2xhdGVfbG9ncw==').decode()}` "
                f"should be called "
                f"`hours`."
        )
        
    def test_function_exists_join_tables(self):
        functions = _get_function_names(self.MODULE)
        self.assertIn(
            base64.b64decode(b'am9pbl90YWJsZXM=').decode(),
            functions,
            msg=f"The function "
                f"`{base64.b64decode(b'am9pbl90YWJsZXM=').decode()}` "
                f"is not found, but it was marked as required."
        )
        
    def test_function_signature_match_join_tables(self):
        functions = _get_function_names(self.MODULE)
        self.assertIn(
            base64.b64decode(b'am9pbl90YWJsZXM=').decode(),
            functions,
            msg=f"The function "
                f"`{base64.b64decode(b'am9pbl90YWJsZXM=').decode()}` "
                f"is not found, but it was marked as required."
        )
        args = _get_function_arg_names(
            self.MODULE,
            base64.b64decode(b'am9pbl90YWJsZXM=').decode()
        )
        self.assertEqual(
            3,
            len(args),
            msg=f"The function "
                f"`{base64.b64decode(b'am9pbl90YWJsZXM=').decode()}` "
                f"should have exactly 3 argument(s)."
        )
        args = _get_function_arg_names(
            self.MODULE,
            base64.b64decode(b'am9pbl90YWJsZXM=').decode()
        )
        self.assertEqual(
            base64.b64decode(b'bG9ncw==').decode(),
            args[0],
            msg=f"The argument #0 of function "
                f"`{base64.b64decode(b'am9pbl90YWJsZXM=').decode()}` "
                f"should be called "
                f"`logs`."
        )
        args = _get_function_arg_names(
            self.MODULE,
            base64.b64decode(b'am9pbl90YWJsZXM=').decode()
        )
        self.assertEqual(
            base64.b64decode(b'ZXhwZXJpbWVudHM=').decode(),
            args[1],
            msg=f"The argument #1 of function "
                f"`{base64.b64decode(b'am9pbl90YWJsZXM=').decode()}` "
                f"should be called "
                f"`experiments`."
        )
        args = _get_function_arg_names(
            self.MODULE,
            base64.b64decode(b'am9pbl90YWJsZXM=').decode()
        )
        self.assertEqual(
            base64.b64decode(b'bWV0cmljcw==').decode(),
            args[2],
            msg=f"The argument #2 of function "
                f"`{base64.b64decode(b'am9pbl90YWJsZXM=').decode()}` "
                f"should be called "
                f"`metrics`."
        )
        
    def test_function_exists_load_experiments(self):
        functions = _get_function_names(self.MODULE)
        self.assertIn(
            base64.b64decode(b'bG9hZF9leHBlcmltZW50cw==').decode(),
            functions,
            msg=f"The function "
                f"`{base64.b64decode(b'bG9hZF9leHBlcmltZW50cw==').decode()}` "
                f"is not found, but it was marked as required."
        )
        
    def test_function_signature_match_load_experiments(self):
        functions = _get_function_names(self.MODULE)
        self.assertIn(
            base64.b64decode(b'bG9hZF9leHBlcmltZW50cw==').decode(),
            functions,
            msg=f"The function "
                f"`{base64.b64decode(b'bG9hZF9leHBlcmltZW50cw==').decode()}` "
                f"is not found, but it was marked as required."
        )
        args = _get_function_arg_names(
            self.MODULE,
            base64.b64decode(b'bG9hZF9leHBlcmltZW50cw==').decode()
        )
        self.assertEqual(
            1,
            len(args),
            msg=f"The function "
                f"`{base64.b64decode(b'bG9hZF9leHBlcmltZW50cw==').decode()}` "
                f"should have exactly 1 argument(s)."
        )
        args = _get_function_arg_names(
            self.MODULE,
            base64.b64decode(b'bG9hZF9leHBlcmltZW50cw==').decode()
        )
        self.assertEqual(
            base64.b64decode(b'ZXhwZXJpbWVudHNfcGF0aA==').decode(),
            args[0],
            msg=f"The argument #0 of function "
                f"`{base64.b64decode(b'bG9hZF9leHBlcmltZW50cw==').decode()}` "
                f"should be called "
                f"`experiments_path`."
        )
        
    def test_function_exists_load_logs(self):
        functions = _get_function_names(self.MODULE)
        self.assertIn(
            base64.b64decode(b'bG9hZF9sb2dz').decode(),
            functions,
            msg=f"The function "
                f"`{base64.b64decode(b'bG9hZF9sb2dz').decode()}` "
                f"is not found, but it was marked as required."
        )
        
    def test_function_signature_match_load_logs(self):
        functions = _get_function_names(self.MODULE)
        self.assertIn(
            base64.b64decode(b'bG9hZF9sb2dz').decode(),
            functions,
            msg=f"The function "
                f"`{base64.b64decode(b'bG9hZF9sb2dz').decode()}` "
                f"is not found, but it was marked as required."
        )
        args = _get_function_arg_names(
            self.MODULE,
            base64.b64decode(b'bG9hZF9sb2dz').decode()
        )
        self.assertEqual(
            1,
            len(args),
            msg=f"The function "
                f"`{base64.b64decode(b'bG9hZF9sb2dz').decode()}` "
                f"should have exactly 1 argument(s)."
        )
        args = _get_function_arg_names(
            self.MODULE,
            base64.b64decode(b'bG9hZF9sb2dz').decode()
        )
        self.assertEqual(
            base64.b64decode(b'bG9nc19wYXRo').decode(),
            args[0],
            msg=f"The argument #0 of function "
                f"`{base64.b64decode(b'bG9hZF9sb2dz').decode()}` "
                f"should be called "
                f"`logs_path`."
        )
        
    def test_function_exists_load_metrics(self):
        functions = _get_function_names(self.MODULE)
        self.assertIn(
            base64.b64decode(b'bG9hZF9tZXRyaWNz').decode(),
            functions,
            msg=f"The function "
                f"`{base64.b64decode(b'bG9hZF9tZXRyaWNz').decode()}` "
                f"is not found, but it was marked as required."
        )
        
    def test_function_signature_match_load_metrics(self):
        functions = _get_function_names(self.MODULE)
        self.assertIn(
            base64.b64decode(b'bG9hZF9tZXRyaWNz').decode(),
            functions,
            msg=f"The function "
                f"`{base64.b64decode(b'bG9hZF9tZXRyaWNz').decode()}` "
                f"is not found, but it was marked as required."
        )
        args = _get_function_arg_names(
            self.MODULE,
            base64.b64decode(b'bG9hZF9tZXRyaWNz').decode()
        )
        self.assertEqual(
            0,
            len(args),
            msg=f"The function "
                f"`{base64.b64decode(b'bG9hZF9tZXRyaWNz').decode()}` "
                f"should have exactly 0 argument(s)."
        )
        
    def test_function_exists_save(self):
        functions = _get_function_names(self.MODULE)
        self.assertIn(
            base64.b64decode(b'c2F2ZQ==').decode(),
            functions,
            msg=f"The function "
                f"`{base64.b64decode(b'c2F2ZQ==').decode()}` "
                f"is not found, but it was marked as required."
        )
        
    def test_function_signature_match_save(self):
        functions = _get_function_names(self.MODULE)
        self.assertIn(
            base64.b64decode(b'c2F2ZQ==').decode(),
            functions,
            msg=f"The function "
                f"`{base64.b64decode(b'c2F2ZQ==').decode()}` "
                f"is not found, but it was marked as required."
        )
        args = _get_function_arg_names(
            self.MODULE,
            base64.b64decode(b'c2F2ZQ==').decode()
        )
        self.assertEqual(
            2,
            len(args),
            msg=f"The function "
                f"`{base64.b64decode(b'c2F2ZQ==').decode()}` "
                f"should have exactly 2 argument(s)."
        )
        args = _get_function_arg_names(
            self.MODULE,
            base64.b64decode(b'c2F2ZQ==').decode()
        )
        self.assertEqual(
            base64.b64decode(b'ZGF0YQ==').decode(),
            args[0],
            msg=f"The argument #0 of function "
                f"`{base64.b64decode(b'c2F2ZQ==').decode()}` "
                f"should be called "
                f"`data`."
        )
        args = _get_function_arg_names(
            self.MODULE,
            base64.b64decode(b'c2F2ZQ==').decode()
        )
        self.assertEqual(
            base64.b64decode(b'b3V0cHV0X3BhdGg=').decode(),
            args[1],
            msg=f"The argument #1 of function "
                f"`{base64.b64decode(b'c2F2ZQ==').decode()}` "
                f"should be called "
                f"`output_path`."
        )
        

# === Internal functions, do not modify ===
import inspect

from types import ModuleType
from typing import List


def _get_function_names(module: ModuleType) -> List[str]:
    names = []
    functions = inspect.getmembers(module, lambda member: inspect.isfunction(member))
    for name, fn in functions:
        if fn.__module__ == module.__name__:
            names.append(name)
    return names


def _get_function_arg_names(module: ModuleType, fn_name: str) -> List[str]:
    arg_names = []
    functions = inspect.getmembers(module, lambda member: inspect.isfunction(member))
    for name, fn in functions:
        if fn.__module__ == module.__name__:
            if fn.__qualname__ == fn_name:
                args_spec = inspect.getfullargspec(fn)
                arg_names = args_spec.args
                if args_spec.varargs is not None:
                    arg_names.extend(args_spec.varargs)
                if args_spec.varkw is not None:
                    arg_names.extend(args_spec.varkw)
                arg_names.extend(args_spec.kwonlyargs)
                break
    return arg_names


def _get_class_names(module: ModuleType) -> List[str]:
    names = []
    classes = inspect.getmembers(module, lambda member: inspect.isclass(member))
    for name, cls in classes:
        if cls.__module__ == module.__name__:
            names.append(name)
    return names


def _get_class_function_names(module: ModuleType, cls_name: str) -> List[str]:
    fn_names = []
    classes = inspect.getmembers(module, lambda member: inspect.isclass(member))
    for cls_name_, cls in classes:
        if cls.__module__ == module.__name__:
            if cls_name_ == cls_name:
                functions = inspect.getmembers(
                    cls,
                    lambda member: inspect.ismethod(member)
                    or inspect.isfunction(member),
                )
                for fn_name, fn in functions:
                    fn_names.append(fn.__qualname__)
                break
    return fn_names


def _get_class_function_arg_names(
    module: ModuleType, cls_name: str, fn_name: str
) -> List[str]:
    arg_names = []
    classes = inspect.getmembers(module, lambda member: inspect.isclass(member))
    for cls_name_, cls in classes:
        if cls.__module__ == module.__name__:
            if cls_name_ == cls_name:
                functions = inspect.getmembers(
                    cls,
                    lambda member: inspect.ismethod(member)
                    or inspect.isfunction(member),
                )
                for fn_name_, fn in functions:
                    if fn.__qualname__ == fn_name:
                        args_spec = inspect.getfullargspec(fn)
                        arg_names = args_spec.args
                        if args_spec.varargs is not None:
                            arg_names.extend(args_spec.varargs)
                        if args_spec.varkw is not None:
                            arg_names.extend(args_spec.varkw)
                        arg_names.extend(args_spec.kwonlyargs)
                        break
                break
    return arg_names
